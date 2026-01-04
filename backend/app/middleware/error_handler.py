import logging
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def error_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]):
    """Global error handler for standardized error responses."""
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": getattr(exc, "error_code", None),
            }
        )
    
    # Log unexpected errors
    logger.exception("Unexpected error occurred")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        }
    )

