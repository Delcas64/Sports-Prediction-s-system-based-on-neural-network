from fastapi import APIRouter
from app.services.nba_api import get_upcoming_matches

router = APIRouter(prefix="/matches")

@router.get("/upcoming")
def upcoming_matches(limit: int = 10):
    return get_upcoming_matches(limit)
