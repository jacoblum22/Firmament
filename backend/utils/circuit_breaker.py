"""
Circuit breaker pattern implementation for external service calls
Helps prevent cascade failures when external services are down
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict, Type, Union
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    pass


import threading
from typing import Optional, Union, Type


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Union[Type[Exception], tuple] = Exception,
        name: str = "CircuitBreaker",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        self._lock = threading.RLock()

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def reset(self):
        """Reset circuit breaker to closed state"""
        with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        """Check if function can be executed based on circuit state"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (
                self.last_failure_time
                and (time.time() - self.last_failure_time) >= self.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self):
        """Record successful execution"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker {self.name} closing - service recovered")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        """Record failed execution"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker {self.name} opening - {self.failure_count} failures"
                )
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN")

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise e

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN")

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise e

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }


# Global circuit breakers for different services
openai_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception,
    name="OpenAI_API",
)

redis_circuit_breaker = CircuitBreaker(
    failure_threshold=5, recovery_timeout=15, expected_exception=Exception, name="Redis"
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=45,
    expected_exception=Exception,
    name="Database",
)


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers"""
    return {
        "openai": openai_circuit_breaker.get_stats(),
        "redis": redis_circuit_breaker.get_stats(),
        "database": database_circuit_breaker.get_stats(),
    }
