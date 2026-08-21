from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.chat import ChatRequest, ChatResponse, chat
from app.core.database import get_db
from app.services.llm import provider_status
from app.services.tutor import TUTOR_ACTIONS

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    """Provider availability only — API keys never leave the backend."""
    return {**provider_status(), "tutorActions": TUTOR_ACTIONS}


@router.post("/tutor", response_model=ChatResponse)
async def tutor(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Personalized tutor endpoint (same engine as POST /api/chat)."""
    return await chat(request, db)
