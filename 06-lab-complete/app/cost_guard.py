"""
Cost guard (tiêu chí 8).

Yêu cầu:
  • Cộng dồn chi phí LLM (tính theo token) vào Redis
  • Tổng chi phí vượt DAILY_BUDGET_USD (hoặc MONTHLY_BUDGET_USD) → HTTP 402
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError

from .config import settings
from .redis_client import r

# Giá USD / 1K tokens (tham khảo gpt-4o-mini)
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006

def _redis_client() -> Redis:
    if r is None:
        raise HTTPException(status_code=503, detail="Redis is unavailable")
    return r


def _budget_key() -> str:
    day = datetime.now(timezone.utc).date().isoformat()
    return f"llm-cost:{day}"


def check_budget() -> None:
    client = _redis_client()
    try:
        used_usd = float(client.get(_budget_key()) or 0)
    except RedisError as exc:
        raise HTTPException(
            status_code=503, detail="Redis is unavailable"
        ) from exc

    if used_usd >= settings.daily_budget_usd:
        raise HTTPException(status_code=402, detail="Daily budget exceeded")


def record_cost(input_tokens: int, output_tokens: int) -> float:
    cost_usd = (
        input_tokens * PRICE_INPUT_PER_1K
        + output_tokens * PRICE_OUTPUT_PER_1K
    ) / 1000

    client = _redis_client()
    key = _budget_key()
    try:
        with client.pipeline(transaction=True) as pipe:
            pipe.incrbyfloat(key, cost_usd)
            pipe.expire(key, 2 * 24 * 60 * 60)
            pipe.execute()
    except RedisError as exc:
        raise HTTPException(
            status_code=503, detail="Redis is unavailable"
        ) from exc

    return cost_usd
