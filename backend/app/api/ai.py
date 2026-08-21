from fastapi import APIRouter
from app.services.llm import provider_status

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    return provider_status()
