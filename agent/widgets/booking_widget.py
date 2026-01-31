"""Booking confirmation widget with Stripe checkout button."""

from typing import Any
from chatkit.widgets import Card, CardSection, CardItem


def build_booking_widget(
    start_date: str,
    end_date: str,
    guests: int,
    nights: int,
    nightly_rate: int,
    cleaning_fee: int,
    total_cents: int,
    action_type: str = "booking.pay",
) -> Card:
    """Build a booking confirmation card with payment button."""

    total_dollars = total_cents / 100
    nights_total = nightly_rate * nights

    return Card(
        title="Booking Summary",
        sections=[
            CardSection(
                items=[
                    CardItem(label="Check-in", value=start_date),
                    CardItem(label="Check-out", value=end_date),
                    CardItem(label="Guests", value=str(guests)),
                ]
            ),
            CardSection(
                title="Price Breakdown",
                items=[
                    CardItem(label=f"${nightly_rate} × {nights} nights", value=f"${nights_total}"),
                    CardItem(label="Cleaning fee", value=f"${cleaning_fee}"),
                    CardItem(label="Total", value=f"${total_dollars:.0f}", emphasis=True),
                ]
            ),
        ],
        actions=[
            {
                "type": action_type,
                "label": "Pay Now",
                "handler": "server",
                "payload": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "guests": guests,
                    "total_cents": total_cents,
                },
            }
        ],
    )
