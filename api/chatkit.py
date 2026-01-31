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
        from chatkit.server import StreamingResult
        from agent.server import BookingChatServer
        chatkit_server = BookingChatServer()
    return chatkit_server


@app.get("/api/chatkit")
async def health():
    return {
        "status": "ok",
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    }


@app.get("/api/chatkit/test-agent")
async def test_agent():
    """Test agent directly to debug issues"""
    import traceback
    try:
        from agent.server import BookingChatServer
        server = BookingChatServer()

        # Test agent creation
        agent = server.agent
        return {
            "status": "ok",
            "agent_name": agent.name,
            "agent_model": agent.model,
            "num_tools": len(agent.tools) if agent.tools else 0,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/api/chatkit")
async def chatkit(request: Request):
    try:
        from chatkit.server import StreamingResult
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
