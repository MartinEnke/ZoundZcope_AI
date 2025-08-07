# token_tracker.py

from threading import Lock

# Pricing (as of Aug 2025, check OpenAI for latest)
PRICES = {
    "gpt-4o-mini": 0.0005 / 1000,  # $0.0005 per 1K tokens
    "gpt-4o": 0.005 / 1000         # $0.005 per 1K tokens
}

token_lock = Lock()
_token_usage = {
    "total_tokens": 0,
    "total_cost": 0.0
}


def add_token_usage(token_count: int, model_name: str = "gpt-4o-mini"):
    with token_lock:
        price_per_token = PRICES.get(model_name, PRICES["gpt-4o-mini"])
        _token_usage["total_tokens"] += token_count
        _token_usage["total_cost"] += token_count * price_per_token


def get_token_usage():
    with token_lock:
        return {
            "total_tokens": _token_usage["total_tokens"],
            "total_cost": round(_token_usage["total_cost"], 6)
        }


def reset_token_usage():
    with token_lock:
        _token_usage["total_tokens"] = 0
        _token_usage["total_cost"] = 0.0
