import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import get_logger


logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        request_id = str(uuid.uuid4())[:8]

        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.info(
            "[%s] REQUEST START | %s %s",
            request_id,
            request.method,
            request.url.path
        )

        try:

            response = await call_next(request)

            duration = time.perf_counter() - start_time

            logger.info(
                "[%s] REQUEST END | Status: %s | Time: %.3fs",
                request_id,
                response.status_code,
                duration
            )

            response.headers["X-Request-ID"] = request_id

            return response

        except Exception:

            duration = time.perf_counter() - start_time

            logger.exception(
                "[%s] REQUEST FAILED | %s %s | Time: %.3fs",
                request_id,
                request.method,
                request.url.path,
                duration
            )

            raise