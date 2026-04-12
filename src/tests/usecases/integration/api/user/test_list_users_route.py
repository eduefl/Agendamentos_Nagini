
"""
Testes de integração para a rota GET /users/ (list_users).

Cobre:
- Listagem bem-sucedida (response 200)
- Exceção mapeada corretamente pelo error handler
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from domain.user.user_exceptions import UserNotFoundError


class TestListUsersRoute:
    def test_list_users_returns_200(self, client: TestClient):
        response = client.get("/users/")
        assert response.status_code == 200
        body = response.json()
        assert "json" in body
        assert "xml" in body
        assert isinstance(body["json"], list)

    def test_list_users_exception_is_handled(self, client: TestClient):
        with patch(
            "infrastructure.api.routers.user_routers.ListUsersUseCase.execute",
            side_effect=UserNotFoundError("not-found"),
        ):
            response = client.get("/users/")
        assert response.status_code == 404
