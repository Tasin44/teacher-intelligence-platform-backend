import logging

from django.utils import timezone
from rest_framework.views import exception_handler

from rest_framework.exceptions import Throttled

logger = logging.getLogger("aamyproject")


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        wait = getattr(exc, "wait", None)
        return _wrap(
            message=f"Too many requests. Try again in {wait}s." if wait else "Too many requests.",
            status_code=429,
            data=None,
        )

    if response is not None:
        message = "Request failed"
        if isinstance(response.data, dict):
            from coreapp.response import StandardResponseMixin
            message = StandardResponseMixin().extract_first_error(response.data) or message
        return _wrap(message=message, status_code=response.status_code, data=response.data)

    logger.exception("Unhandled exception: %s", exc)
    return _wrap(message="Internal server error", status_code=500, data=None)

def _wrap(message, status_code, data):
    from rest_framework.response import Response
    return Response({
        "success": False,
        "statusCode": status_code,
        "message": message,
        "data": data,
        "timestamp": timezone.now().isoformat(),
    }, status=status_code)
