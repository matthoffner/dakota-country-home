"""
Vercel Serverless Function: ChatKit Endpoint

This proxies ChatKit requests to the booking agent.
Vercel runs this as a Python serverless function.
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import sys
import os

# Add parent directory to path so we can import agent module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.server import BookingChatServer
from chatkit.server import StreamingResult

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatkit_server = BookingChatServer()


@app.get("/api/chatkit")
async def health():
    return {"status": "ok"}


@app.post("/api/chatkit")
async def chatkit_endpoint(request: Request) -> Response:
    """ChatKit endpoint - handles conversation with booking agent."""
    payload = await request.body()
    result = await chatkit_server.process(payload, {"request": request})

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")

    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")

    return JSONResponse(result)
