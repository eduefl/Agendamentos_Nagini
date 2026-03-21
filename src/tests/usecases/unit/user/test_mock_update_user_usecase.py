from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.user.user_entity import User
from domain.user.user_exceptions import EmailAlreadyExistsError, UserNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.update_user.update_user_dto import UpdateUserInputDTO
from usecases.user.update_user.update_user_usecase import updateUserUsecase


class TestMockUpdateUserUseCase:
    def test_mock_update_user_usecase(self):
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

        use_case = updateUserUsecase(mock_user_repository)

        input_dto = UpdateUserInputDTO(
            id=user_id,
            name="Jane Doe",
            email="jane@example.com",
            is_active=False,
        )
        output = use_case.execute(input_dto)

        assert output.id == user_id
        assert output.name == "Jane Doe"
        assert str(output.email) == "jane@example.com"
        assert output.is_active is False

        # se o DTO de saída tiver roles, valida também:
        if hasattr(output, "roles"):
            assert output.roles == ["cliente"]

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_user_repository.update_user.assert_called_once()

        # como a chamada é keyword: update_user(user=user)
		# args, kwargs = mock_user_repository.update_user.call_args
        _, kwargs = mock_user_repository.update_user.call_args
        updated_user = kwargs["user"]

        assert isinstance(updated_user, User)
        assert updated_user.id == user_id
        assert updated_user.name == "Jane Doe"
        assert updated_user.email == "jane@example.com"
        assert updated_user.is_active is False

        # senha não deve mudar nesse use case
        assert updated_user.hashed_password == "hashed"
        # roles também não deve mudar nesse use case
        assert updated_user.roles == {"cliente"}

    def test_mock_update_user_usecase_user_not_found(self):
        mock_user_repository = MagicMock(spec=userRepositoryInterface)

        user_id = uuid4()
        mock_user_repository.find_user_by_id.side_effect = UserNotFoundError(user_id)

        use_case = updateUserUsecase(mock_user_repository)

        input_dto = UpdateUserInputDTO(
            id=user_id,
            name="Jane Doe",
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_user_repository.update_user.assert_not_called()

    def test_mock_update_user_usecase_email_already_exists(self):
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

        # simula conflito de email no update
        mock_user_repository.update_user.side_effect = EmailAlreadyExistsError(
            "dup@example.com"
        )

        use_case = updateUserUsecase(mock_user_repository)

        input_dto = UpdateUserInputDTO(
            id=user_id,
            email="dup@example.com",
        )

        with pytest.raises(EmailAlreadyExistsError, match="dup@example.com"):
            use_case.execute(input_dto)

        mock_user_repository.find_user_by_id.assert_called_once_with(user_id=user_id)
        mock_user_repository.update_user.assert_called_once()

        # opcional: validar que o user enviado já veio com o email alterado
        args, kwargs = mock_user_repository.update_user.call_args
        updated_user = kwargs.get("user") or args[0]
        assert updated_user.email == "dup@example.com"
        # senha continua igual
        assert updated_user.hashed_password == "hashed"
        # roles continua igual
        assert updated_user.roles == {"cliente"}