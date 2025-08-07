from fastapi import APIRouter
from pydantic import BaseModel
from app.token_tracker import add_token_usage, get_token_usage, reset_token_usage

router = APIRouter()

class TokenInput(BaseModel):
    tokens: int
    model: str = "gpt-4o-mini"

@router.get("/api/token-stats")
def get_stats():
    return get_token_usage()

@router.post("/api/add-token-usage")
def add_stats(data: TokenInput):
    add_token_usage(data.tokens, data.model)
    return {"status": "ok"}

@router.post("/api/reset-token-stats")
def reset_stats():
    reset_token_usage()
    return {"status": "reset"}
