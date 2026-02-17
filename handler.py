from fastapi import Request
from browser import BrowserManager
import asyncio

bm = BrowserManager()

async def init_browser():
    await bm.init_browser()

async def chat_completions(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    prompt = messages[-1]["content"] if messages else ""

    async def stream_generator():
        async for chunk in bm.send_message(prompt):
            yield f'data: {{"choices": [{{"delta": {{"content": "{chunk}"}}}}]}}\n\n'
        yield "data: [DONE]\n\n"

    return stream_generator()