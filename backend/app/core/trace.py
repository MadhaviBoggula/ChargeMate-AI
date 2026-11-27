import inspect
import time

from functools import wraps

from app.core.logger import get_logger


def trace_execution(func):

    logger = get_logger(func.__module__)

    function_name = func.__qualname__

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):

            start = time.perf_counter()

            logger.debug("ENTER: %s", function_name)

            try:

                result = await func(*args, **kwargs)

                logger.debug(
                    "EXIT: %s | Time: %.3fs",
                    function_name,
                    time.perf_counter() - start
                )

                return result

            except Exception:

                logger.exception(
                    "FAILED: %s",
                    function_name
                )

                raise

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args, **kwargs):

        start = time.perf_counter()

        logger.debug("ENTER: %s", function_name)

        try:

            result = func(*args, **kwargs)

            logger.debug(
                "EXIT: %s | Time: %.3fs",
                function_name,
                time.perf_counter() - start
            )

            return result

        except Exception:

            logger.exception(
                "FAILED: %s",
                function_name
            )

            raise

    return sync_wrapper