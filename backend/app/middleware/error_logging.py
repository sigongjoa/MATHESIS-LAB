"""
Global error logging middleware for all unhandled exceptions.

NOTE: This middleware has been simplified to remove try-except blocks.
FastAPI's built-in exception handlers will now handle all errors directly.
If you need custom error logging, configure Python logging at the application level
instead of using middleware to catch exceptions.

For detailed error logging, use:
1. Python's logging configuration in main.py
2. FastAPI's exception handlers (app.exception_handler)
3. Structured logging libraries (structlog, python-json-logger)

This middleware is now a NO-OP placeholder and can be removed.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware placeholder - no longer catches exceptions.

    All exceptions now propagate naturally to FastAPI's exception handlers.
    Configure error logging in main.py instead.
    """

    async def dispatch(self, request: Request, call_next):
        # Simply pass through - no error catching
        # All errors will propagate to FastAPI's default handlers
        response = await call_next(request)
        return response
