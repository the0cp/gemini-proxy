import json
import time
import uuid
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse
from browser import BrowserManager
import asyncio

bm = BrowserManager()

async def init_browser():
    await bm.init_browser()

async def chat_completions(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    
    prompt_text = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt_text += f"[System Instructions]\n{content}\n\n"
        elif role == "user":
            prompt_text += f"[User Request]\n{content}\n\n"
    prompt = prompt_text.strip()
    
    stream = data.get("stream", False)
    model = data.get("model", "gemini-1.5-pro")

    chat_id = f"chatcmpl-{uuid.uuid4().hex}"
    created_time = int(time.time())

    if stream:
        async def stream_generator():
            initial_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"

            async for chunk in bm.send_message(prompt):
                response_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": model,
                    "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(response_chunk)}\n\n"
            
            final_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    
    else:
        full_content = ""
        async for chunk in bm.send_message(prompt):
            full_content += chunk
            
        response_data = {
            "id": chat_id,
            "object": "chat.completion",
            "created": created_time,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        return JSONResponse(content=response_data)