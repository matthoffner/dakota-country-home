"""ChatKit server for Dakota Country Home booking agent."""

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

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

BOOKING_INSTRUCTIONS = """
You are the booking assistant for Dakota Country Home, a beautiful vacation rental.

## Your Role
Guide guests through booking their stay. Ask one question at a time. Be concise but warm.

## Booking Flow
1. Greet and ask about their trip (dates, number of guests)
2. Check availability using get_availability tool
3. If available, get quote using get_quote tool
4. Show quote and ask for email
5. Create checkout using create_stripe_checkout tool

## Property Details
- Sleeps up to 10 guests
- Minimum 2 night stay
- $250/night + $150 cleaning fee
- Beautiful Dakota countryside

## Rules
- Never invent availability or prices - always use the tools
- If unavailable, suggest nearby dates
- Keep responses concise
"""


def get_availability_tool(start_date: str, end_date: str) -> dict:
    """Check if dates are available. Args: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)"""
    return check_availability(start_date, end_date)


def get_quote_tool(start_date: str, end_date: str, guests: int) -> dict:
    """Get pricing quote. Args: start_date, end_date (YYYY-MM-DD), guests (number)"""
    return calculate_quote(start_date, end_date, guests)


def create_stripe_checkout_tool(
    amount_cents: int,
    customer_email: str,
    start_date: str,
    end_date: str,
    guests: int
) -> dict:
    """Create Stripe checkout. Args: amount_cents, customer_email, start_date, end_date, guests"""
    return create_checkout_session(
        amount_cents=amount_cents,
        customer_email=customer_email,
        metadata={"start_date": start_date, "end_date": end_date, "guests": str(guests)},
    )


booking_agent = Agent[AgentContext[dict[str, Any]]](
    model=MODEL,
    name="Dakota Country Home",
    instructions=BOOKING_INSTRUCTIONS,
    tools=[get_availability_tool, get_quote_tool, create_stripe_checkout_tool],
)


class BookingChatServer(ChatKitServer[dict[str, Any]]):
    def __init__(self):
        self.store = BookingStore()
        super().__init__(self.store)

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        items_page = await self.store.load_thread_items(thread.id, None, 50, "desc", context)
        items = list(reversed(items_page.data))
        agent_input = await simple_to_agent_input(items)

        agent_context = AgentContext(thread=thread, store=self.store, request_context=context)
        result = Runner.run_streamed(booking_agent, agent_input, context=agent_context)

        async for event in stream_agent_response(agent_context, result):
            yield event
