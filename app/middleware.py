import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger: logging.Logger) -> None:
        super().__init__(app)
        self._logger = logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.time()
        path = request.url.path
        method = request.method
        client = request.client.host if request.client else "-"
        self._logger.info("%s %s from %s", method, path, client)
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed = int((time.time() - start) * 1000)
            self._logger.info("%s %s -> %s in %sms", method, path, getattr(response, "status_code", "-"), elapsed)


