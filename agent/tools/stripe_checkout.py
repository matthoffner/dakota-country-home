"""
Stripe Embedded Checkout integration.

Creates checkout sessions for in-chat payment.
"""

import os
from typing import Optional
import stripe


# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Your domain for return URLs
DOMAIN = os.getenv("SITE_DOMAIN", "http://localhost:3000")


def create_checkout_session(
    amount_cents: int,
    customer_email: str,
    metadata: dict,
    description: Optional[str] = None,
    currency: str = "usd"
) -> dict:
    """
    Create a Stripe Embedded Checkout session.

    Args:
        amount_cents: Amount in cents
        customer_email: Customer's email
        metadata: Booking metadata (dates, guests, etc.)
        description: Line item description
        currency: Currency code (default: usd)

    Returns:
        {
            "session_id": str,
            "client_secret": str,  # For embedded checkout
            "status": "created"
        }
    """
    if not stripe.api_key:
        return {
            "error": "Stripe not configured",
            "session_id": None
        }

    try:
        # Create checkout session for embedded mode
        session = stripe.checkout.Session.create(
            mode="payment",
            ui_mode="embedded",  # For embedded checkout
            customer_email=customer_email,
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": "Dakota Country Home Stay",
                            "description": description or "Vacation rental booking",
                        },
                    },
                    "quantity": 1,
                }
            ],
            metadata=metadata,
            return_url=f"{DOMAIN}?session_id={{CHECKOUT_SESSION_ID}}&status=complete",
            # Automatic tax calculation (optional)
            # automatic_tax={"enabled": True},
        )

        return {
            "session_id": session.id,
            "client_secret": session.client_secret,
            "status": "created",
            "amount_cents": amount_cents,
            "currency": currency,
        }

    except stripe.error.StripeError as e:
        return {
            "error": str(e),
            "session_id": None
        }


def get_session_status(session_id: str) -> dict:
    """
    Get the status of a checkout session.

    Args:
        session_id: Stripe session ID

    Returns:
        Session status and payment details
    """
    if not stripe.api_key:
        return {"error": "Stripe not configured"}

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        return {
            "session_id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "customer_email": session.customer_email,
            "amount_total": session.amount_total,
            "currency": session.currency,
            "metadata": dict(session.metadata) if session.metadata else {},
        }

    except stripe.error.StripeError as e:
        return {
            "error": str(e),
            "session_id": session_id
        }
