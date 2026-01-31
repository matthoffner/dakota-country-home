"""
Availability checking via Airbnb iCal integration.
"""

import os
from datetime import datetime, date
from typing import Optional
import urllib.request

ICAL_URL = os.getenv("AIRBNB_ICAL_URL")

_ical_cache = {"data": None, "fetched_at": None}
CACHE_TTL_SECONDS = 300


def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def fetch_ical():
    """Fetch and parse Airbnb iCal feed."""
    if not ICAL_URL:
        return None

    now = datetime.now()
    if _ical_cache["data"] and _ical_cache["fetched_at"]:
        age = (now - _ical_cache["fetched_at"]).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return _ical_cache["data"]

    try:
        from icalendar import Calendar
        with urllib.request.urlopen(ICAL_URL, timeout=10) as response:
            cal = Calendar.from_ical(response.read())
            _ical_cache["data"] = cal
            _ical_cache["fetched_at"] = now
            return cal
    except Exception as e:
        print(f"Failed to fetch iCal: {e}")
        return _ical_cache["data"]


def get_blocked_dates(cal):
    """Extract blocked date ranges from calendar."""
    blocked = []
    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart = component.get("dtstart")
            dtend = component.get("dtend")
            if dtstart and dtend:
                start = dtstart.dt
                end = dtend.dt
                if isinstance(start, datetime):
                    start = start.date()
                if isinstance(end, datetime):
                    end = end.date()
                blocked.append((start, end))
    return blocked


def check_availability(start_date: str, end_date: str) -> dict:
    """Check if dates are available for booking."""
    try:
        requested_start = parse_date(start_date)
        requested_end = parse_date(end_date)
    except ValueError as e:
        return {"available": False, "blocked_reason": f"Invalid date format: {e}"}

    today = date.today()
    if requested_start < today:
        return {"available": False, "blocked_reason": "Cannot book dates in the past"}

    if requested_end <= requested_start:
        return {"available": False, "blocked_reason": "Check-out must be after check-in"}

    nights = (requested_end - requested_start).days
    if nights < 2:
        return {"available": False, "blocked_reason": "Minimum stay is 2 nights"}

    cal = fetch_ical()
    if cal is None:
        return {"available": True, "blocked_reason": None, "note": "No calendar configured"}

    blocked_ranges = get_blocked_dates(cal)
    for blocked_start, blocked_end in blocked_ranges:
        if requested_start < blocked_end and blocked_start < requested_end:
            return {"available": False, "blocked_reason": f"Dates conflict with existing booking"}

    return {"available": True, "blocked_reason": None}
