"""
Vercel Python Function: ChatKit Booking Agent
"""

import os
import sys

# Add parent dir to path for agent imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from chatkit.server import StreamingResult

from agent.server import BookingChatServer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatkit_server = None

def get_server():
    global chatkit_server
    if chatkit_server is None:
        chatkit_server = BookingChatServer()
    return chatkit_server


@app.get("/api/chatkit")
async def health():
    import os
    return {
        "status": "ok",
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o")
    }


@app.post("/api/chatkit")
async def chatkit(request: Request):
    try:
        server = get_server()
        payload = await request.body()
        result = await server.process(payload, {"request": request})

        if isinstance(result, StreamingResult):
            return StreamingResponse(result, media_type="text/event-stream")
        if hasattr(result, "json"):
            return Response(content=result.json, media_type="application/json")
        return JSONResponse(result)
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)
