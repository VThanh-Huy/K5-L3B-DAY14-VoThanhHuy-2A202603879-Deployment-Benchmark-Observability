"""
Rate limiting (tiêu chí 7).

Yêu cầu:
  • Mỗi API key tối đa RATE_LIMIT_PER_MINUTE request trong 60 giây (sliding window)
  • Vượt giới hạn → HTTP 429, nên kèm header Retry-After
  • State lưu trong Redis để mọi worker / instance dùng chung và vẫn còn sau khi
    restart agent (script chấm sẽ restart agent để kiểm tra)
"""
from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException
from redis.exceptions import RedisError

from .config import settings
from .redis_client import r


SLIDING_WINDOW = """
local clock = redis.call('TIME')
local now = tonumber(clock[1]) * 1000 + math.floor(tonumber(clock[2]) / 1000)
local window_ms = 60000

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window_ms)

if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[1]) then
    local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    return math.ceil((tonumber(oldest[2]) + window_ms - now) / 1000)
end

redis.call('ZADD', KEYS[1], now, ARGV[2])
redis.call('PEXPIRE', KEYS[1], window_ms)
return 0
"""


def check_rate_limit(key: str) -> None:
    if r is None:
        raise HTTPException(status_code=503, detail="Redis is unavailable")

    key_hash = sha256(key.encode("utf-8")).hexdigest()

    try:
        retry_after = r.eval(
            SLIDING_WINDOW,
            1,
            f"rate-limit:{key_hash}",
            settings.rate_limit_per_minute,
            uuid4().hex,
        )
    except RedisError as exc:
        raise HTTPException(
            status_code=503, detail="Redis is unavailable"
        ) from exc

    if retry_after > 0:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
