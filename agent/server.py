"""
ChatKit server for Dakota Country Home booking agent.

This connects the booking agent to the ChatKit frontend,
handling conversation state and streaming responses.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from agents import Agent, Runner
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import ThreadMetadata, ThreadStreamEvent, UserMessageItem

from .store import BookingStore
from .tools.availability import check_availability
from .tools.pricing import calculate_quote
from .tools.stripe_checkout import create_checkout_session


MAX_RECENT_ITEMS = 50
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


# Agent system instructions
BOOKING_INSTRUCTIONS = """
You are the booking assistant for Dakota Country Home, a beautiful vacation rental.

## Your Role
Guide guests through booking their stay in a friendly, conversational manner.
Ask one question at a time. Be concise but warm.

## Booking Flow
1. Greet the guest and ask about their trip (dates, number of guests)
2. Once you have dates, check availability using the get_availability tool
3. If available, get a quote using the get_quote tool
4. Show the quote and ask for their email to proceed
5. Create checkout using create_stripe_checkout tool
6. Confirm the checkout was created and guide them to complete payment

## Property Details
- Sleeps up to 10 guests
- Minimum 2 night stay
- Nightly rate: $250
- Cleaning fee: $150
- Located in the beautiful Dakota countryside

## Important Rules
- Never invent availability - always call get_availability
- Never invent prices - always call get_quote
- If dates are unavailable, suggest checking nearby dates
- Be helpful if guests have questions about the property
- Keep responses concise - this is a chat interface

## Formatting
- Use short paragraphs
- When showing quotes, format as a clear breakdown
- Be conversational, not formal

## Tone
Friendly, professional, and helpful. Like a knowledgeable host who wants
guests to have a great experience.
"""


def get_availability_tool(start_date: str, end_date: str) -> dict:
    """
    Check if the requested dates are available for booking.

    Args:
        start_date: Check-in date in YYYY-MM-DD format
        end_date: Check-out date in YYYY-MM-DD format
    """
    return check_availability(start_date, end_date)


def get_quote_tool(start_date: str, end_date: str, guests: int) -> dict:
    """
    Calculate pricing for a stay.

    Args:
        start_date: Check-in date in YYYY-MM-DD format
        end_date: Check-out date in YYYY-MM-DD format
        guests: Number of guests
    """
    return calculate_quote(start_date, end_date, guests)


def create_stripe_checkout_tool(
    amount_cents: int,
    customer_email: str,
    start_date: str,
    end_date: str,
    guests: int,
    description: str = None
) -> dict:
    """
    Create a Stripe Embedded Checkout session for payment.

    Args:
        amount_cents: Total amount in cents (e.g., 65000 for $650.00)
        customer_email: Guest's email address
        start_date: Check-in date in YYYY-MM-DD format
        end_date: Check-out date in YYYY-MM-DD format
        guests: Number of guests
        description: Optional description for the charge
    """
    return create_checkout_session(
        amount_cents=amount_cents,
        customer_email=customer_email,
        metadata={
            "start_date": start_date,
            "end_date": end_date,
            "guests": str(guests),
        },
        description=description or f"Stay at Dakota Country Home ({start_date} to {end_date})"
    )


# Create the booking agent with tools
booking_agent = Agent[AgentContext[dict[str, Any]]](
    model=MODEL,
    name="Dakota Country Home Booking Assistant",
    instructions=BOOKING_INSTRUCTIONS,
    tools=[get_availability_tool, get_quote_tool, create_stripe_checkout_tool],
)


class BookingChatServer(ChatKitServer[dict[str, Any]]):
    """ChatKit server for the booking agent."""

    def __init__(self) -> None:
        self.store = BookingStore()
        super().__init__(self.store)

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle incoming messages and stream agent responses."""

        # Load conversation history
        items_page = await self.store.load_thread_items(
            thread.id,
            after=None,
            limit=MAX_RECENT_ITEMS,
            order="desc",
            context=context,
        )
        items = list(reversed(items_page.data))

        # Convert to agent input format
        agent_input = await simple_to_agent_input(items)

        # Create agent context
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        # Run the agent and stream responses
        result = Runner.run_streamed(
            booking_agent,
            agent_input,
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event
