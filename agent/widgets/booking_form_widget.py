"""Booking form widget with DatePicker, Select, and Input."""

import json
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Template

# Load widget template
WIDGET_PATH = Path(__file__).parent / "booking_form.widget"
with open(WIDGET_PATH) as f:
    BOOKING_FORM_WIDGET = json.load(f)


def build_booking_form(
    checkin: str = "",
    checkout: str = "",
    guests: str = "",
    email: str = "",
) -> dict:
    """Build booking form widget with pre-filled values.

    Returns a widget JSON structure that can be sent to ChatKit.
    """
    # Minimum date is tomorrow
    min_date = (date.today() + timedelta(days=1)).isoformat()

    # Render template with values
    template = Template(BOOKING_FORM_WIDGET["template"])
    rendered = template.render(
        min_date=min_date,
        checkin=checkin,
        checkout=checkout,
        guests=guests,
        email=email,
    )

    return json.loads(rendered)
