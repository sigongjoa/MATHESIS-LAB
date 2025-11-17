"""
Global error logging middleware for all unhandled exceptions.

This middleware logs all unhandled exceptions at the ERROR level with full traceback,
ensuring visibility into production issues.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all unhandled exceptions with full context.

    This ensures that even if a route has try-except blocks, any exception
    that escapes them is logged with:
    - Full traceback
    - Request path and method
    - Timestamp
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the exception with full traceback
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "request_query": str(request.url.query),
                    "exception_type": type(e).__name__,
                }
            )

            # Re-raise to let FastAPI handle the response
            raise
