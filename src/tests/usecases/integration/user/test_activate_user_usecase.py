from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from domain.user.user_exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActiveError,
    UserNotFoundError,
)
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.activate_user.activate_user_dto import (
    ActivateUserInputDTO,
    ActivateUserOutputDTO,
)
from usecases.user.activate_user.activate_user_usecase import ActivateUserUseCase


class TestActivateUserUseCaseIntegration:
    def test_activate_user_success(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        raw_code = "abc12345"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=False,
            activation_code=hasher.hash(raw_code),
            activation_code_expires_at=expires_at,
            roles={"cliente"},
        )
        repository.add_user(user=user)

        use_case = ActivateUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = ActivateUserInputDTO(
            email="john@example.com",
            activation_code=raw_code,
        )

        output = use_case.execute(input=input_dto)

        assert isinstance(output, ActivateUserOutputDTO)
        assert isinstance(output.id, UUID)
        assert output.id == user.id
        assert output.name == "John Doe"
        assert str(output.email) == "john@example.com"
        assert output.is_active is True
        assert output.roles == ["cliente"]

        updated_user = repository.find_user_by_id(user_id=user.id)
        assert updated_user.is_active is True
        assert updated_user.activation_code is None
        assert updated_user.activation_code_expires_at is None
        assert updated_user.roles == {"cliente"}

    def test_activate_user_raises_when_user_not_found(self, tst_db_session):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        use_case = ActivateUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = ActivateUserInputDTO(
            email="missing@example.com",
            activation_code="abc12345",
        )

        with pytest.raises(UserNotFoundError):
            use_case.execute(input=input_dto)

    def test_activate_user_raises_when_user_already_active(
        self, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=True,
            activation_code=hasher.hash("abc12345"),
            activation_code_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            roles={"cliente"},
        )
        repository.add_user(user=user)

        use_case = ActivateUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = ActivateUserInputDTO(
            email="john@example.com",
            activation_code="abc12345",
        )

        with pytest.raises(UserAlreadyActiveError, match="john@example.com"):
            use_case.execute(input=input_dto)

        persisted = repository.find_user_by_id(user_id=user.id)
        assert persisted.is_active is True

    def test_activate_user_raises_when_activation_code_is_missing(
        self, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        repository.add_user(user=user)

        use_case = ActivateUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = ActivateUserInputDTO(
            email="john@example.com",
            activation_code="abc12345",
        )

        with pytest.raises(InvalidActivationCodeError):
            use_case.execute(input=input_dto)

        persisted = repository.find_user_by_id(user_id=user.id)
        assert persisted.is_active is False
        assert persisted.activation_code is None
        assert persisted.activation_code_expires_at is None

    def test_activate_user_raises_when_activation_code_is_expired(
        self, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=False,
            activation_code=hasher.hash("abc12345"),
            activation_code_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            roles={"cliente"},
        )
        repository.add_user(user=user)

        use_case = ActivateUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = ActivateUserInputDTO(
            email="john@example.com",
            activation_code="abc12345",
        )

        with pytest.raises(ActivationCodeExpiredError):
            use_case.execute(input=input_dto)

        persisted = repository.find_user_by_id(user_id=user.id)
        assert persisted.is_active is False
        assert persisted.activation_code is not None
        assert persisted.activation_code_expires_at is not None

    def test_activate_user_raises_when_activation_code_is_invalid(
        self, tst_db_session, make_user, seed_roles
    ):
        session = tst_db_session
        repository = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        user = make_user(
            name="John Doe",
            email="john@example.com",
            is_active=False,
            activation_code=hasher.hash("abc12345"),
            activation_code_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            roles={"cliente"},
        )
        repository.add_user(user=user)

        use_case = ActivateUserUseCase(
            user_repository=repository,
            password_hasher=hasher,
        )

        input_dto = ActivateUserInputDTO(
            email="john@example.com",
            activation_code="wrong-code",
        )

        with pytest.raises(InvalidActivationCodeError):
            use_case.execute(input=input_dto)

        persisted = repository.find_user_by_id(user_id=user.id)
        assert persisted.is_active is False
        assert persisted.activation_code is not None
        assert persisted.activation_code_expires_at is not None