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


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token_provider) -> None:
        super().__init__(app)
        self._get_token = token_provider

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Always allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        token = self._get_token()
        path = request.url.path or "/"
        # Enforce bearer auth only for tool endpoints
        if token and path.startswith("/tools"):
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer ") or auth_header.split(" ", 1)[1] != token:
                return Response(status_code=401, content=b"Unauthorized")
        return await call_next(request)


