from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config import settings
import time


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
    """Simple rate limiting middleware"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        if settings.environment == "production":
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()

            # Clean old entries
            self.clients = {
                ip: (count, timestamp)
                for ip, (count, timestamp) in self.clients.items()
                if current_time - timestamp < self.period
            }

            # Check rate limit
            if client_ip in self.clients:
                count, timestamp = self.clients[client_ip]
                if current_time - timestamp < self.period:
                    if count >= self.calls:
                        return JSONResponse(
                            status_code=429, content={"detail": "Rate limit exceeded"}
                        )
                    self.clients[client_ip] = (count + 1, timestamp)
                else:
                    self.clients[client_ip] = (1, current_time)
            else:
                self.clients[client_ip] = (1, current_time)

        return await call_next(request)
