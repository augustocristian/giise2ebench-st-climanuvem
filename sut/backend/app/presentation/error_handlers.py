from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match
from http import HTTPStatus

PROBLEM_JSON = "application/problem+json"


def _problem(status: int, detail, headers=None) -> JSONResponse:
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = "Error"
    return JSONResponse(
        status_code=status,
        content={"type": "about:blank", "title": title, "status": status, "detail": detail},
        media_type=PROBLEM_JSON,
        headers=headers,
    )


PROBED_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def _allowed_methods(request: Request) -> str:
    """Union of the methods accepted by every route whose path matches the request path.

    Starlette only reports the first partial match in ``Allow``; probe each method
    against the routers instead (independent of how the framework nests routers).
    """
    methods: set[str] = set()
    for method in PROBED_METHODS:
        for route in request.app.router.routes:
            scope = {
                "type": "http",
                "path": request.scope["path"],
                "root_path": request.scope.get("root_path", ""),
                "method": method,
            }
            if route.matches(scope)[0] == Match.FULL:
                methods.add(method)
                break
    return ", ".join(sorted(methods))


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    headers = getattr(exc, "headers", None)
    if exc.status_code == 405:
        allow = _allowed_methods(request)
        if allow:
            headers = {**(headers or {}), "Allow": allow}
    detail = exc.detail
    if detail == HTTPStatus(exc.status_code).phrase:
        # Framework-generated errors (404 route, 405...) get a machine code too.
        detail = HTTPStatus(exc.status_code).phrase.upper().replace(" ", "_")
    return _problem(exc.status_code, detail, headers)


async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return _problem(422, jsonable_encoder(exc.errors()))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
