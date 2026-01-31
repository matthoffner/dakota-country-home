"""
FastAPI entrypoint for the Dakota Country Home booking agent.

This exposes the ChatKit server endpoint that the frontend connects to.
"""

from __future__ import annotations

import os
from chatkit.server import StreamingResult
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .server import BookingChatServer

# Create FastAPI app
app = FastAPI(
    title="Dakota Country Home Booking API",
    description="ChatKit-powered booking agent for vacation rental",
    version="1.0.0",
)

# Configure CORS
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the ChatKit server instance
chatkit_server = BookingChatServer()


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "booking-agent"}


@app.post("/chatkit")
async def chatkit_endpoint(request: Request) -> Response:
    """
    Main ChatKit endpoint.

    Receives messages from the ChatKit frontend and streams
    responses from the booking agent.
    """
    payload = await request.body()
    result = await chatkit_server.process(payload, {"request": request})

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")

    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")

    return JSONResponse(result)


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
