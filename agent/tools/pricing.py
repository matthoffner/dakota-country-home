"""
Pricing calculator for Dakota Country Home.

Simple pricing model:
- Base nightly rate
- Cleaning fee (flat)
- Optional: extra guest fees, seasonal rates, etc.
"""

import os
from datetime import datetime, date
from typing import Optional


# Pricing configuration (could come from env or config file)
NIGHTLY_RATE = int(os.getenv("NIGHTLY_RATE", "250"))  # $250/night
CLEANING_FEE = int(os.getenv("CLEANING_FEE", "150"))  # $150 flat
MAX_GUESTS = int(os.getenv("MAX_GUESTS", "10"))
EXTRA_GUEST_FEE = int(os.getenv("EXTRA_GUEST_FEE", "0"))  # Per night, per extra guest
BASE_GUESTS = int(os.getenv("BASE_GUESTS", "6"))  # Guests included in base rate


def parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD string to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def calculate_quote(start_date: str, end_date: str, guests: int) -> dict:
    """
    Calculate pricing for a stay.

    Args:
        start_date: Check-in date (YYYY-MM-DD)
        end_date: Check-out date (YYYY-MM-DD)
        guests: Number of guests

    Returns:
        {
            "nights": int,
            "nightly_rate": int,
            "accommodation_total": int,
            "cleaning_fee": int,
            "extra_guest_fee": int,
            "total": int,
            "currency": "usd",
            "breakdown": str
        }
    """
    try:
        check_in = parse_date(start_date)
        check_out = parse_date(end_date)
    except ValueError as e:
        return {
            "error": f"Invalid date format: {e}",
            "nights": 0,
            "total": 0
        }

    # Calculate nights
    nights = (check_out - check_in).days

    if nights <= 0:
        return {
            "error": "Check-out must be after check-in",
            "nights": 0,
            "total": 0
        }

    # Validate guests
    if guests > MAX_GUESTS:
        return {
            "error": f"Maximum {MAX_GUESTS} guests allowed",
            "nights": nights,
            "total": 0
        }

    if guests < 1:
        return {
            "error": "At least 1 guest required",
            "nights": nights,
            "total": 0
        }

    # Calculate base accommodation
    accommodation_total = nights * NIGHTLY_RATE

    # Calculate extra guest fees
    extra_guests = max(0, guests - BASE_GUESTS)
    extra_guest_total = extra_guests * EXTRA_GUEST_FEE * nights

    # Total
    total = accommodation_total + CLEANING_FEE + extra_guest_total

    # Build breakdown string
    breakdown_lines = [
        f"${NIGHTLY_RATE} x {nights} nights = ${accommodation_total}"
    ]
    if extra_guest_total > 0:
        breakdown_lines.append(
            f"Extra guest fee ({extra_guests} guests) = ${extra_guest_total}"
        )
    breakdown_lines.append(f"Cleaning fee = ${CLEANING_FEE}")
    breakdown_lines.append(f"Total = ${total}")

    return {
        "nights": nights,
        "guests": guests,
        "nightly_rate": NIGHTLY_RATE,
        "accommodation_total": accommodation_total,
        "cleaning_fee": CLEANING_FEE,
        "extra_guest_fee": extra_guest_total,
        "total": total,
        "total_cents": total * 100,
        "currency": "usd",
        "breakdown": "\n".join(breakdown_lines),
        "dates": {
            "check_in": start_date,
            "check_out": end_date
        }
    }
