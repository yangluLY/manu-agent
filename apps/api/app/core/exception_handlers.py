from fastapi import Request
from fastapi.responses import JSONResponse

from apps.api.app.core.exceptions import (
    AppException,
)


async def app_exception_handler(
    _request: Request,
    exc: AppException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )
