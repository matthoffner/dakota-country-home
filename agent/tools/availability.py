"""
Availability checking via Airbnb iCal integration.

Fetches the iCal feed and checks for date conflicts.
"""

import os
from datetime import datetime, date, timedelta
from typing import Optional
import urllib.request
from icalendar import Calendar


ICAL_URL = os.getenv("AIRBNB_ICAL_URL")

# Cache for iCal data (simple in-memory, refreshes every 5 min)
_ical_cache = {
    "data": None,
    "fetched_at": None,
}
CACHE_TTL_SECONDS = 300  # 5 minutes


def parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD string to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def fetch_ical() -> Optional[Calendar]:
    """Fetch and parse the Airbnb iCal feed."""
    if not ICAL_URL:
        return None

    now = datetime.now()

    # Check cache
    if _ical_cache["data"] and _ical_cache["fetched_at"]:
        age = (now - _ical_cache["fetched_at"]).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return _ical_cache["data"]

    try:
        with urllib.request.urlopen(ICAL_URL, timeout=10) as response:
            ical_data = response.read()
            cal = Calendar.from_ical(ical_data)
            _ical_cache["data"] = cal
            _ical_cache["fetched_at"] = now
            return cal
    except Exception as e:
        print(f"Failed to fetch iCal: {e}")
        # Return cached data if available, even if stale
        return _ical_cache["data"]


def get_blocked_dates(cal: Calendar) -> list[tuple[date, date]]:
    """Extract blocked date ranges from calendar."""
    blocked = []

    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart = component.get("dtstart")
            dtend = component.get("dtend")

            if dtstart and dtend:
                start = dtstart.dt
                end = dtend.dt

                # Convert datetime to date if needed
                if isinstance(start, datetime):
                    start = start.date()
                if isinstance(end, datetime):
                    end = end.date()

                blocked.append((start, end))

    return blocked


def dates_overlap(
    start1: date, end1: date,
    start2: date, end2: date
) -> bool:
    """Check if two date ranges overlap."""
    # Ranges overlap if one starts before the other ends
    return start1 < end2 and start2 < end1


def check_availability(start_date: str, end_date: str) -> dict:
    """
    Check if dates are available for booking.

    Args:
        start_date: Check-in date (YYYY-MM-DD)
        end_date: Check-out date (YYYY-MM-DD)

    Returns:
        {
            "available": bool,
            "blocked_reason": str | None,
            "checked_dates": {"start": str, "end": str}
        }
    """
    try:
        requested_start = parse_date(start_date)
        requested_end = parse_date(end_date)
    except ValueError as e:
        return {
            "available": False,
            "blocked_reason": f"Invalid date format: {e}",
            "checked_dates": {"start": start_date, "end": end_date}
        }

    # Validate date range
    today = date.today()
    if requested_start < today:
        return {
            "available": False,
            "blocked_reason": "Cannot book dates in the past",
            "checked_dates": {"start": start_date, "end": end_date}
        }

    if requested_end <= requested_start:
        return {
            "available": False,
            "blocked_reason": "Check-out must be after check-in",
            "checked_dates": {"start": start_date, "end": end_date}
        }

    nights = (requested_end - requested_start).days
    if nights < 2:
        return {
            "available": False,
            "blocked_reason": "Minimum stay is 2 nights",
            "checked_dates": {"start": start_date, "end": end_date}
        }

    # Fetch calendar
    cal = fetch_ical()

    if cal is None:
        # No iCal configured - assume available (for demo purposes)
        return {
            "available": True,
            "blocked_reason": None,
            "checked_dates": {"start": start_date, "end": end_date},
            "note": "No calendar configured - availability not verified"
        }

    # Check for conflicts
    blocked_ranges = get_blocked_dates(cal)

    for blocked_start, blocked_end in blocked_ranges:
        if dates_overlap(requested_start, requested_end, blocked_start, blocked_end):
            return {
                "available": False,
                "blocked_reason": f"Dates conflict with existing booking ({blocked_start} to {blocked_end})",
                "checked_dates": {"start": start_date, "end": end_date}
            }

    return {
        "available": True,
        "blocked_reason": None,
        "checked_dates": {"start": start_date, "end": end_date}
    }
