"""
Token usage tracking endpoints for ZoundZcope.

This module provides API endpoints to view, update, and reset token usage
statistics for the application's GPT model interactions. These endpoints
interact with the token tracker utility to maintain accurate usage metrics.

Endpoints:
    GET    /api/token-stats
        Retrieve current token usage statistics.

    POST   /api/add-token-usage
        Add token usage for a specific model.

    POST   /api/reset-token-stats
        Reset all token usage statistics to zero.

Dependencies:
    - token_tracker utility functions:
        * add_token_usage
        * get_token_usage
        * reset_token_usage
    - Pydantic for request body validation (TokenInput).
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.token_tracker import add_token_usage, get_token_usage, reset_token_usage

router = APIRouter()


class TokenInput(BaseModel):
    """
        Request body model for adding token usage.

        Attributes:
            tokens (int): Number of tokens to add.
            model (str): Model name associated with the token usage.
                Defaults to "gpt-4o-mini".
        """
    tokens: int
    model: str = "gpt-4o-mini"


@router.get("/api/token-stats")
def get_stats():
    """
        Retrieve current token usage statistics.

        Returns:
            dict: Token usage data, including totals per model.
        """
    return get_token_usage()


@router.post("/api/add-token-usage")
def add_stats(data: TokenInput):
    """
        Add token usage for a specified model.

        Args:
            data (TokenInput): Number of tokens and model name.

        Returns:
            dict: Status confirmation.
        """
    add_token_usage(data.tokens, data.model)
    return {"status": "ok"}


@router.post("/api/reset-token-stats")
def reset_stats():
    """
        Reset all tracked token usage statistics to zero.

        Returns:
            dict: Status confirmation of reset.
        """
    reset_token_usage()
    return {"status": "reset"}
