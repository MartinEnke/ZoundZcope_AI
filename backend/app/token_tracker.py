"""
Token usage tracking utilities for ZoundZcope.

This module tracks the total tokens consumed and estimated cost for AI model usage.
It supports:
    - Adding token usage for a given model.
    - Retrieving cumulative usage and cost.
    - Resetting usage statistics.

Thread safety:
    A threading.Lock is used to ensure atomic updates to usage counters.

Pricing:
    - Prices are stored per 1000 tokens in the `PRICES` dictionary.
    - Default model is "gemini-2.5-flash" unless otherwise specified.

IMPORTANT:
    The prices below are placeholders. Update them with the current Gemini pricing
    you want your app to reflect.
"""

from threading import Lock

# Pricing per 1000 tokens (PLACEHOLDERS — update if you want real cost estimates)
PRICES = {
    "gemini-2.5-flash": 0.0,
    "gemini-2.5-pro": 0.0,
}

DEFAULT_MODEL = "gemini-2.5-flash"

token_lock = Lock()
_token_usage = {
    "total_tokens": 0,
    "total_cost": 0.0
}


def add_token_usage(token_count: int, model_name: str = DEFAULT_MODEL):
    """
    Record additional token usage for a given model.

    Args:
        token_count (int): Number of tokens used.
        model_name (str, optional): Model identifier.
            Defaults to DEFAULT_MODEL. Falls back to default pricing if unknown.

    Thread Safety:
        Uses a lock to ensure consistent updates to shared counters.
    """
    if not isinstance(token_count, int) or token_count < 0:
        return

    with token_lock:
        price_per_1k = PRICES.get(model_name, PRICES.get(DEFAULT_MODEL, 0.0))
        _token_usage["total_tokens"] += token_count
        _token_usage["total_cost"] += (token_count / 1000) * price_per_1k


def get_token_usage():
    """
    Retrieve the current total token usage and cost.

    Returns:
        dict: {
            "total_tokens" (int): Total tokens recorded.
            "total_cost" (float): Rounded total cost.
        }

    Thread Safety:
        Uses a lock to ensure a consistent read of shared counters.
    """
    with token_lock:
        return {
            "total_tokens": _token_usage["total_tokens"],
            "total_cost": round(_token_usage["total_cost"], 5)
        }


def reset_token_usage():
    """
    Reset all token usage statistics to zero.

    Thread Safety:
        Uses a lock to ensure counters are reset atomically.
    """
    with token_lock:
        _token_usage["total_tokens"] = 0
        _token_usage["total_cost"] = 0.0