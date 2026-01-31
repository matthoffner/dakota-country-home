"""ChatKit server for Dakota Country Home booking agent."""

import os
from datetime import datetime
from typing import Any, AsyncIterator

from agents import Agent, Runner, function_tool, RunContextWrapper
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import (
    Action,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
    AssistantMessageItem,
    AssistantMessageContent,
    ThreadItemDoneEvent,
    ClientEffectEvent,
)

from .store import BookingStore
from .tools.availability import check_availability
from .tools.pricing import calculate_quote
from .tools.stripe_checkout import create_checkout_session
from .widgets.booking_widget import build_booking_widget

BOOKING_INSTRUCTIONS = """
You are the booking assistant for Dakota Country Home, a beautiful vacation rental.

## Your Role
Guide guests through booking their stay. Ask one question at a time. Be concise but warm.

## Booking Flow
1. Greet and ask about their trip (dates, number of guests)
2. Check availability using get_availability tool
3. If available, get quote using get_quote tool
4. Ask for their email address for the booking confirmation
5. Once you have the email, use show_payment_form to display the credit card form

## Property Details
- Sleeps up to 10 guests
- Minimum 2 night stay
- $250/night + $150 cleaning fee
- Beautiful Dakota countryside

## Rules
- Never invent availability or prices - always use the tools
- If unavailable, suggest nearby dates
- You MUST collect the customer's email before showing the payment form
- After getting email, IMMEDIATELY call show_payment_form to display the embedded payment form
- Keep responses concise
"""


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
        tools=[get_availability, get_quote, show_payment_form],
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
