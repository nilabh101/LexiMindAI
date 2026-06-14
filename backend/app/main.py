"""LexiMind AI — FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import documents, analysis
from app.api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="LexiMind AI API",
    description="Document Intelligence Platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)


class LimitUploadSize(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and "upload" in str(request.url):
            cl = request.headers.get("content-length")
            if cl and int(cl) > 600 * 1024 * 1024:
                return JSONResponse({"detail": "File too large. Max 500 MB."}, status_code=413)
        return await call_next(request)


app.add_middleware(LimitUploadSize)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routers mounted under /api
app.include_router(documents.router, prefix="/api")   # → /api/documents/...
app.include_router(analysis.router,  prefix="/api")   # → /api/analysis/...
app.include_router(chat_router,      prefix="/api")   # → /api/chat/...


@app.get("/")
def root():
    return {"message": "LexiMind AI API v2.0 — Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
