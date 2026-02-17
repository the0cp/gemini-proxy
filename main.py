from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from handler import chat_completions, init_browser
from contextlib import asynccontextmanager
import uvicorn
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_browser()
    yield
    if hasattr(init_browser, 'bm'): 
        await init_browser.bm.close() 

app = FastAPI(title="Gemini Web Proxy", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/v1/chat/completions")
@limiter.limit(f"{settings.MAX_REQUESTS_PER_MIN}/minute")
async def completions(request: Request):
    return StreamingResponse(await chat_completions(request), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok", "browser": "ready"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.LOG_LEVEL)