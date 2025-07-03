from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config import settings
import time
import redis
import json
import logging
from typing import Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if settings.environment == "production":
            # Security headers for production
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = "default-src 'self'"

            # HSTS header for HTTPS
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed rate limiting middleware with proper IP detection"""

    def __init__(
        self, app, calls: int = 100, period: int = 60, redis_url: Optional[str] = None
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period

        # Initialize Redis connection or fallback to in-memory with LRU cache
        self.redis_client = None
        self.fallback_to_memory = False

        try:
            if redis_url or settings.redis_url:
                self.redis_client = redis.from_url(
                    redis_url or settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis rate limiting enabled")
            else:
                self.fallback_to_memory = True
                logger.warning(
                    "Redis URL not configured, falling back to in-memory rate limiting"
                )
        except Exception as e:
            logger.error(
                f"Failed to connect to Redis: {e}, falling back to in-memory rate limiting"
            )
            self.redis_client = None
            self.fallback_to_memory = True

        # In-memory fallback with LRU cache (max 10000 entries)
        if self.fallback_to_memory:
            self._memory_cache = {}
            self._max_memory_entries = 10000

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP, handling proxies and load balancers"""

        # Check X-Forwarded-For header (most common proxy header)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first (original client)
            client_ip = forwarded_for.split(",")[0].strip()
            if client_ip and client_ip != "unknown":
                return client_ip

        # Check X-Real-IP header (Nginx proxy)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip and real_ip != "unknown":
            return real_ip

        # Check CF-Connecting-IP header (Cloudflare)
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip and cf_ip != "unknown":
            return cf_ip

        # Check X-Client-IP header
        client_ip_header = request.headers.get("X-Client-IP")
        if client_ip_header and client_ip_header != "unknown":
            return client_ip_header

        # Fallback to direct connection IP
        if request.client and request.client.host:
            return request.client.host

        return "unknown"

    def _redis_key(self, client_ip: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{client_ip}:{int(time.time() // self.period)}"

    async def _check_rate_limit_redis(self, client_ip: str) -> Tuple[bool, int]:
        """Check rate limit using Redis"""
        try:
            if self.redis_client is None:
                logger.error("Redis client is None, falling back to allowing request")
                return True, 0

            key = self._redis_key(client_ip)

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.period)
            results = pipe.execute()

            current_count = results[0]

            if current_count > self.calls:
                return False, current_count

            return True, current_count

        except Exception as e:
            logger.error(
                f"Redis rate limit check failed: {e}, falling back to allowing request"
            )
            return True, 0

    def _check_rate_limit_memory(self, client_ip: str) -> Tuple[bool, int]:
        """Check rate limit using in-memory cache with LRU eviction"""
        current_time = time.time()

        # Clean expired entries and enforce max size
        if len(self._memory_cache) > self._max_memory_entries:
            # Remove oldest entries (simple LRU implementation)
            sorted_items = sorted(
                self._memory_cache.items(), key=lambda x: x[1].get("last_access", 0)
            )
            # Remove oldest 20% of entries
            entries_to_remove = len(sorted_items) // 5
            for i in range(entries_to_remove):
                del self._memory_cache[sorted_items[i][0]]

        # Clean expired entries
        expired_keys = [
            ip
            for ip, data in self._memory_cache.items()
            if current_time - data["timestamp"] > self.period
        ]
        for key in expired_keys:
            del self._memory_cache[key]

        # Check current client
        if client_ip in self._memory_cache:
            data = self._memory_cache[client_ip]
            if current_time - data["timestamp"] < self.period:
                if data["count"] >= self.calls:
                    return False, data["count"]

                # Update count and last access
                self._memory_cache[client_ip] = {
                    "count": data["count"] + 1,
                    "timestamp": data["timestamp"],
                    "last_access": current_time,
                }
                return True, data["count"] + 1

        # New or expired entry
        self._memory_cache[client_ip] = {
            "count": 1,
            "timestamp": current_time,
            "last_access": current_time,
        }
        return True, 1

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc"]:
            return await call_next(request)

        # Only apply rate limiting in production or if explicitly enabled
        if settings.environment == "production" or getattr(
            settings, "enable_rate_limiting", False
        ):
            client_ip = self._get_client_ip(request)

            # Check rate limit
            if self.redis_client and not self.fallback_to_memory:
                is_allowed, count = await self._check_rate_limit_redis(client_ip)
            else:
                is_allowed, count = self._check_rate_limit_memory(client_ip)

            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded for IP {client_ip}: {count} requests in {self.period}s"
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": self.period,
                        "limit": self.calls,
                        "period": self.period,
                    },
                    headers={
                        "Retry-After": str(self.period),
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": str(max(0, self.calls - count)),
                        "X-RateLimit-Reset": str(int(time.time()) + self.period),
                    },
                )

            # Add rate limit headers to successful responses
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - count))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)

            return response

        return await call_next(request)
