from fastapi import Request, HTTPException
import time
from typing import Dict, Tuple
import asyncio
from app.core.settings import get_settings

settings = get_settings()

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, Tuple[int, float]] = {}
        self.lock = asyncio.Lock()

    async def is_rate_limited(self, key: str) -> bool:
        async with self.lock:
            current_time = time.time()
            if key in self.requests:
                requests, window_start = self.requests[key]
                if current_time - window_start >= 1.0:  # 1 second window
                    self.requests[key] = (1, current_time)
                    return False
                if requests >= settings.RATE_LIMIT_PER_SECOND:
                    return True
                self.requests[key] = (requests + 1, window_start)
                return False
            self.requests[key] = (1, current_time)
            return False

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    # Get client IP or API key for rate limiting
    client_key = request.client.host
    
    # Check rate limit
    if await rate_limiter.is_rate_limited(client_key):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
    
    # Add rate limit headers
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_SECOND)
    
    return response
