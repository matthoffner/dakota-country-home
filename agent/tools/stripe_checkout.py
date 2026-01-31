"""Stripe Embedded Checkout integration."""

import os
from typing import Optional
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("SITE_DOMAIN", "http://localhost:3000")


def create_checkout_session(
    amount_cents: int,
    customer_email: str,
    metadata: dict,
    description: Optional[str] = None,
    currency: str = "usd"
) -> dict:
    """Create a Stripe Embedded Checkout session."""
    if not stripe.api_key:
        return {"error": "Stripe not configured", "session_id": None}

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            ui_mode="embedded",
            customer_email=customer_email,
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": "Dakota Country Home Stay",
                        "description": description or "Vacation rental booking",
                    },
                },
                "quantity": 1,
            }],
            metadata=metadata,
            return_url=f"{DOMAIN}?session_id={{CHECKOUT_SESSION_ID}}&status=complete",
        )

        return {
            "session_id": session.id,
            "client_secret": session.client_secret,
            "status": "created",
        }

    except stripe.error.StripeError as e:
        return {"error": str(e), "session_id": None}
