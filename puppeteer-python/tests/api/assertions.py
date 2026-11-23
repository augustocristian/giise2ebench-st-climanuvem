"""Assertions shared by the API tests."""
import requests


def assert_problem(response: requests.Response, status: int, detail: str) -> None:
    """Asserts the uniform ``application/problem+json`` error: HTTP status and machine-code ``detail``."""
    assert response.status_code == status, f"HTTP status (body: {response.text})"
    assert response.headers["Content-Type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == status, "problem 'status'"
    assert body["detail"] == detail, "problem 'detail' machine code"


def assert_unauthenticated(response: requests.Response) -> None:
    """Asserts ``401 NOT_AUTHENTICATED`` with a Bearer challenge."""
    assert_problem(response, 401, "NOT_AUTHENTICATED")
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


def assert_method_not_allowed(response: requests.Response, *allowed_methods: str) -> None:
    """Asserts a 405 response whose ``Allow`` header lists every given method."""
    assert response.status_code == 405
    allow = {method.strip().upper() for method in response.headers.get("Allow", "").split(",") if method.strip()}
    assert allow >= set(allowed_methods), f"Allow header: {sorted(allow)}"
