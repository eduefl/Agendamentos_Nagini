from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.user.user_entity import User
from domain.user.user_exceptions import UserNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdInputDTO
from usecases.user.find_user_by_id.find_user_by_id_usecase import FindUserByIdUseCase


class TestFindUserByIdUseCase:
    def test_find_user_by_id(self):
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        user_id = uuid4()

        mock_user_repository.find_user_by_id.return_value = User(
            id=user_id,
            name="John Doe",
            email="john@example.com",
            hashed_password="hashed",
            is_active=True,
            roles={"cliente"},
        )


        use_case = FindUserByIdUseCase(mock_user_repository)

        input_dto = findUserByIdInputDTO(id=user_id)
        output = use_case.execute(input=input_dto)

        assert output.id == user_id
        assert output.name == "John Doe"
        assert str(output.email) == "john@example.com"
        assert output.is_active is True
        assert output.roles == ["cliente"]

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)

    def test_find_user_by_id_raises_when_user_not_found(self):
        user_id = uuid4()
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(user_id)

        use_case = FindUserByIdUseCase(mock_user_repository)
        input_dto = findUserByIdInputDTO(id=user_id)

        with pytest.raises(UserNotFoundError):
            use_case.execute(input=input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
