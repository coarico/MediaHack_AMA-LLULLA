import pytest

from app.core.security import UnsafeUrlError, validate_public_http_url


def test_rejects_localhost() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_http_url("http://localhost:8000")


def test_rejects_private_ip() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_http_url("http://127.0.0.1:8000")

