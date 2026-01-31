"""Pricing calculator for Dakota Country Home."""

import os
from datetime import datetime, date

NIGHTLY_RATE = int(os.getenv("NIGHTLY_RATE", "250"))
CLEANING_FEE = int(os.getenv("CLEANING_FEE", "150"))
MAX_GUESTS = int(os.getenv("MAX_GUESTS", "10"))


def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def calculate_quote(start_date: str, end_date: str, guests: int) -> dict:
    """Calculate pricing for a stay."""
    try:
        check_in = parse_date(start_date)
        check_out = parse_date(end_date)
    except ValueError as e:
        return {"error": f"Invalid date format: {e}", "total": 0}

    nights = (check_out - check_in).days
    if nights <= 0:
        return {"error": "Check-out must be after check-in", "total": 0}

    if guests > MAX_GUESTS:
        return {"error": f"Maximum {MAX_GUESTS} guests allowed", "total": 0}

    accommodation_total = nights * NIGHTLY_RATE
    total = accommodation_total + CLEANING_FEE

    return {
        "nights": nights,
        "guests": guests,
        "nightly_rate": NIGHTLY_RATE,
        "accommodation_total": accommodation_total,
        "cleaning_fee": CLEANING_FEE,
        "total": total,
        "total_cents": total * 100,
        "currency": "usd",
        "breakdown": f"${NIGHTLY_RATE} x {nights} nights = ${accommodation_total}\nCleaning fee = ${CLEANING_FEE}\nTotal = ${total}"
    }
