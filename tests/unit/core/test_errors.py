"""Tests for hwhkit.core.errors."""

from __future__ import annotations

import pytest
from hwhkit.core.errors import (
    ApiError,
    ConflictError,
    DbConnectionError,
    ForbiddenError,
    IntegrationError,
    InternalError,
    NatsConnectionError,
    NotFoundError,
    RateLimitError,
    RedisConnectionError,
    UnauthorizedError,
    ValidationError,
)


class TestApiError:
    def test_base_has_code_and_http_status(self) -> None:
        err = ApiError("something went wrong")
        assert err.code == 500000
        assert err.http_status == 500
        assert err.message == "something went wrong"
        assert err.details == {}

    def test_details_accepted(self) -> None:
        err = ApiError("oops", details={"reason": "x"})
        assert err.details == {"reason": "x"}

    def test_subclasses_have_distinct_codes(self) -> None:
        assert NotFoundError("nf").code == 100404
        assert UnauthorizedError("u").code == 100401
        assert ForbiddenError("f").code == 100403
        assert ValidationError("v").code == 100422
        assert ConflictError("c").code == 100409
        assert RateLimitError("r").code == 100429
        assert InternalError("i").code == 500000
        assert IntegrationError("i").code == 500001
        assert DbConnectionError("d").code == 510001
        assert RedisConnectionError("r").code == 511001
        assert NatsConnectionError("n").code == 512001

    def test_subclasses_have_correct_http_status(self) -> None:
        assert NotFoundError("nf").http_status == 404
        assert UnauthorizedError("u").http_status == 401
        assert ForbiddenError("f").http_status == 403
        assert ValidationError("v").http_status == 422
        assert ConflictError("c").http_status == 409
        assert RateLimitError("r").http_status == 429
        assert InternalError("i").http_status == 500
        assert IntegrationError("i").http_status == 503
        assert DbConnectionError("d").http_status == 503
        assert RedisConnectionError("r").http_status == 503
        assert NatsConnectionError("n").http_status == 503

    def test_code_format_six_digits(self) -> None:
        for cls in [
            NotFoundError,
            UnauthorizedError,
            ForbiddenError,
            ValidationError,
            ConflictError,
            RateLimitError,
            InternalError,
            IntegrationError,
            DbConnectionError,
            RedisConnectionError,
            NatsConnectionError,
        ]:
            assert 100000 <= cls.code <= 999999, f"{cls.__name__}.code not 6-digit"

    def test_is_exception(self) -> None:
        with pytest.raises(ApiError):
            raise NotFoundError("missing")

    def test_business_codes_reserved_range(self) -> None:
        """Codes 600000-899999 reserved for business use."""

        class InsufficientBalance(ApiError):
            code = 620001
            http_status = 400

        err = InsufficientBalance("not enough")
        assert err.code == 620001
        assert err.http_status == 400
