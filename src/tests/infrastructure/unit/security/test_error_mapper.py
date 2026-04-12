"""
Testes para `raise_http_from_error` no módulo _error_mapper.py.

Cobre as linhas que ainda não estavam cobertas:
- HTTPException é repassada diretamente (line 55)
- PaymentGatewayTechnicalFailureError → 503 (line 71)
"""

import pytest
from fastapi import HTTPException, status

from domain.service_request.service_request_exceptions import PaymentGatewayTechnicalFailureError
from infrastructure.api.routers._error_mapper import raise_http_from_error


class TestErrorMapper:
    def test_http_exception_is_reraised_directly(self):
        original = HTTPException(status_code=418, detail="I'm a teapot")
        with pytest.raises(HTTPException) as exc_info:
            raise_http_from_error(original)
        assert exc_info.value.status_code == 418
        assert exc_info.value.detail == "I'm a teapot"

    def test_payment_gateway_technical_failure_returns_503(self):
        err = PaymentGatewayTechnicalFailureError("gateway unavailable")
        with pytest.raises(HTTPException) as exc_info:
            raise_http_from_error(err)
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_unknown_exception_returns_500(self):
        err = RuntimeError("something unexpected")
        with pytest.raises(HTTPException) as exc_info:
            raise_http_from_error(err)
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR