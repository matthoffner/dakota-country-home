"""ChatKit server for Dakota Country Home booking agent."""

import os
from pathlib import Path
from typing import Any, AsyncIterator

from agents import Agent, Runner, function_tool, RunContextWrapper
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.widgets import WidgetTemplate
from chatkit.types import (
    Action,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    ClientEffectEvent,
)

from .store import BookingStore
from .tools.availability import check_availability
from .tools.pricing import calculate_quote
from .tools.stripe_checkout import create_checkout_session

# Load widget templates
WIDGET_DIR = Path(__file__).parent
BOOKING_FORM_TEMPLATE = WidgetTemplate.from_file(str(WIDGET_DIR / "booking_form.widget"))

BOOKING_INSTRUCTIONS = """
You are the booking assistant for Dakota Country Home, a beautiful vacation rental.

## Your Role
Guide guests through booking their stay. Be concise but warm.

## Booking Flow
1. When user wants to book, IMMEDIATELY call show_booking_form to display the interactive form
2. The form has date pickers and guest selector - wait for user to submit
3. After form submission, check availability and show quote
4. Once confirmed, use show_payment_form to display payment

## Property Details
- Sleeps up to 10 guests
- Minimum 2 night stay
- $250/night + $150 cleaning fee
- Beautiful Dakota countryside

## Rules
- ALWAYS use show_booking_form when user wants to book - don't ask for dates in text
- Never invent availability or prices - always use the tools
- If unavailable, suggest nearby dates
- Keep responses concise
"""


@function_tool(description_override="Show the interactive booking form with date pickers and guest selector. Call this when user wants to book a stay.")
async def show_booking_form(
    ctx: RunContextWrapper[AgentContext],
) -> str:
    """Display interactive booking form widget."""
    from datetime import date, timedelta
    min_date = (date.today() + timedelta(days=1)).isoformat()

    # Build and stream the booking form widget inline in the chat
    widget = BOOKING_FORM_TEMPLATE.build({"min_date": min_date})
    await ctx.context.stream_widget(widget)

    return "Booking form displayed. Please fill in your check-in date, check-out date, number of guests, and email, then click Check Availability."


@function_tool(description_override="Check if dates are available for booking. start_date and end_date should be in YYYY-MM-DD format.")
def get_availability(start_date: str, end_date: str) -> dict:
    """Check availability for the given dates."""
    return check_availability(start_date, end_date)


@function_tool(description_override="Get a pricing quote for the stay. start_date and end_date should be in YYYY-MM-DD format, guests is the number of people.")
def get_quote(start_date: str, end_date: str, guests: int) -> dict:
    """Calculate price quote for the booking."""
    return calculate_quote(start_date, end_date, guests)


@function_tool(description_override="Show the embedded Stripe payment form in the chat. Call this after getting a quote and collecting the customer's email.")
async def show_payment_form(
    ctx: RunContextWrapper[AgentContext],
    customer_email: str,
    start_date: str,
    end_date: str,
    guests: int,
    total_cents: int,
) -> str:
    """Display embedded Stripe payment form."""
    # Create Stripe checkout session
    result = create_checkout_session(
        amount_cents=total_cents,
        customer_email=customer_email,
        metadata={
            "start_date": start_date,
            "end_date": end_date,
            "guests": str(guests),
        },
    )

    if result.get("error"):
        return f"Payment error: {result['error']}"

    # Send client effect to render Stripe Elements
    await ctx.context.stream(
        ClientEffectEvent(
            name="stripe_checkout",
            data={
                "client_secret": result["client_secret"],
                "total_cents": total_cents,
                "start_date": start_date,
                "end_date": end_date,
                "guests": guests,
            },
        )
    )

    return "Payment form displayed. Please complete payment."


def create_booking_agent():
    return Agent(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        name="Dakota Country Home",
        instructions=BOOKING_INSTRUCTIONS,
        tools=[show_booking_form, get_availability, get_quote, show_payment_form],
    )


class BookingChatServer(ChatKitServer[dict[str, Any]]):
    def __init__(self):
        self.store = BookingStore()
        self.agent = create_booking_agent()
        super().__init__(self.store)

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        # Load items in desc order and reverse (most recent last)
        items_page = await self.store.load_thread_items(
            thread.id, after=None, limit=20, order="desc", context=context
        )
        items = list(reversed(items_page.data))

        # Convert to agent input format
        input_items = await simple_to_agent_input(items)

        # Create agent context and run with streaming
        agent_context = AgentContext(thread=thread, store=self.store, request_context=context)
        result = Runner.run_streamed(self.agent, input_items, context=agent_context)

        # Stream the response
        async for event in stream_agent_response(agent_context, result):
            yield event

    async def handle_action(
        self,
        thread: ThreadMetadata,
        action: Action,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle form submissions and widget actions."""
        action_type = action.type

        if action_type == "booking.submit":
            # Extract form values
            form_values = action.payload.get("formValues", {})
            checkin = form_values.get("checkin", "")
            checkout = form_values.get("checkout", "")
            guests = form_values.get("guests", "")
            email = form_values.get("email", "")

            # Validate
            if not all([checkin, checkout, guests, email]):
                # Show error message
                from chatkit.types import AssistantMessageItem, TextContent
                yield AssistantMessageItem(
                    id=self.store.generate_item_id("assistant_message", thread, context),
                    content=[TextContent(text="Please fill in all fields: check-in date, check-out date, number of guests, and email.")],
                )
                return

            # Check availability
            availability = check_availability(checkin, checkout)

            if not availability.get("available"):
                from chatkit.types import AssistantMessageItem, TextContent
                yield AssistantMessageItem(
                    id=self.store.generate_item_id("assistant_message", thread, context),
                    content=[TextContent(text=f"Sorry, those dates are not available. {availability.get('message', '')}")],
                )
                return

            # Get quote
            quote = calculate_quote(checkin, checkout, int(guests))

            # Store booking info in thread metadata for later
            thread_data = {
                "checkin": checkin,
                "checkout": checkout,
                "guests": guests,
                "email": email,
                "quote": quote,
            }

            # Show quote and proceed to payment
            from chatkit.types import AssistantMessageItem, TextContent
            nights = quote.get("nights", 0)
            total = quote.get("total_cents", 0) / 100

            message = f"""Great news! Those dates are available.

**Booking Summary:**
- Check-in: {checkin}
- Check-out: {checkout}
- Guests: {guests}
- Nights: {nights}
- Total: ${total:.0f}

I'll now show you the payment form to complete your booking."""

            yield AssistantMessageItem(
                id=self.store.generate_item_id("assistant_message", thread, context),
                content=[TextContent(text=message)],
            )

            # Create Stripe checkout and send effect
            stripe_result = create_checkout_session(
                amount_cents=quote["total_cents"],
                customer_email=email,
                metadata={
                    "start_date": checkin,
                    "end_date": checkout,
                    "guests": guests,
                },
            )

            if not stripe_result.get("error"):
                yield ClientEffectEvent(
                    name="stripe_checkout",
                    data={
                        "client_secret": stripe_result["client_secret"],
                        "total_cents": quote["total_cents"],
                        "start_date": checkin,
                        "end_date": checkout,
                        "guests": int(guests),
                    },
                )

        else:
            # Unknown action, pass to parent
            async for event in super().handle_action(thread, action, context):
                yield event
