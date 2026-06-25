from fastapi import Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core import app, templates
from exceptions import DomainError, InvalidTokenError


# function that does nothing, used for importing in order to ensure this file gets interpreted and registers the handlers
def register_exception_handlers():
    return


# Framework Exceptions


def is_api_request(request: Request) -> bool:
    return request.url.path.startswith("/api")


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(
    request: Request, exception: StarletteHTTPException
):
    if is_api_request(request):
        return await http_exception_handler(request=request, exc=exception)

    message = (
        exception.detail
        or "An error occurred. Please check your request and try again."
    )
    return templates.TemplateResponse(
        request=request,
        name="error.jinja",
        context={
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exception: RequestValidationError
):
    if is_api_request(request):
        return await request_validation_exception_handler(
            request=request, exc=exception
        )

    return templates.TemplateResponse(
        request=request,
        name="error.jinja",
        context={
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


# Domain Exceptions


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    status_code = type(exc).http_status
    if is_api_request(request):
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    title = type(exc).__name__.replace("Error", "").replace("_", " ").title()
    return templates.TemplateResponse(
        request=request,
        name="error.jinja",
        context={
            "status_code": status_code,
            "title": title,
            "message": str(exc),
        },
        status_code=status_code,
    )


@app.exception_handler(InvalidTokenError)
async def invalid_token_handler(request: Request, exception: InvalidTokenError):
    if is_api_request(request):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return templates.TemplateResponse(
        request=request,
        name="error.jinja",
        context={
            "status_code": status.HTTP_401_UNAUTHORIZED,
            "title": "Unauthorized",
            "message": "Invalid or expired token.",
        },
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
