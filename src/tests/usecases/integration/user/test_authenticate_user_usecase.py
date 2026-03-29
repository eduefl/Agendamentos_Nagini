import pytest
from uuid import uuid4

from usecases.user.authenticate_user.authenticate_user_dto import (
    AuthenticateUserInputDTO,
)
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.authenticate_user.authenticate_user_usecase import (
    AuthenticateUserUseCase,
)
from infrastructure.api.factories.make_authenticate_user_usecase import (
    make_authenticate_user_usecase,
)
from domain.user.user_exceptions import InvalidCredentialsError


class TestAuthenticateUserUsecaseIntegration:

    def test_authenticate_user_success(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        user_repoitory = userRepository(session=session)
        hasher = PasslibPasswordHasher()
        token_service = make_token_service()

        user_id = uuid4()
        email_in = "john@example.com"
        password = "Abc12345"
        hash_pass = hasher.hash(password)

        user = make_user(
            id=user_id,
            name="John Doe",
            email=email_in,
            hashed_password=hash_pass,
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repoitory.add_user(user=user)

        use_case = AuthenticateUserUseCase(
            user_repository=user_repoitory,
            password_hasher=hasher,
            tokenService=token_service,
        )

        input_dto = AuthenticateUserInputDTO(email=email_in, password=password)

        # Act
        result = use_case.execute(input_dto)

        # Assert
        assert isinstance(result.access_token, str)
        assert result.token_type == "bearer"
        payload = token_service.decode_token(result.access_token)
        assert payload.sub == user_id
        assert payload.email == email_in
        assert payload.roles == sorted(map(str, user.roles))

    def test_authenticate_user_user_not_found(
        self, tst_db_session, make_user, seed_roles
    ):
        # Arrange
        session = tst_db_session
        email_in = "not@exist.com"

        use_case = make_authenticate_user_usecase(session)

        input_dto = AuthenticateUserInputDTO(email=email_in, password="test_password")

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

    def test_authenticate_user_inactive_user(
        self, tst_db_session, make_user, seed_roles
    ):
        # Arrange
        session = tst_db_session
        user_repoitory = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        user_id = uuid4()
        email_in = "john@example.com"
        password = "Abc12345"
        hash_pass = hasher.hash(password)

        user = make_user(
            id=user_id,
            name="John Doe",
            email=email_in,
            hashed_password=hash_pass,
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},
        )
        user_repoitory.add_user(user=user)

        use_case = make_authenticate_user_usecase(session)

        input_dto = AuthenticateUserInputDTO(email=email_in, password=password)

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)

    def test_authenticate_user_invalid_password(
        self, tst_db_session, make_user, seed_roles
    ):
        # Arrange
        session = tst_db_session
        user_repoitory = userRepository(session=session)
        hasher = PasslibPasswordHasher()

        user_id = uuid4()
        email_in = "john@example.com"
        password = "Abc12345"
        hash_pass = hasher.hash(password)

        user = make_user(
            id=user_id,
            name="John Doe",
            email=email_in,
            hashed_password=hash_pass,
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repoitory.add_user(user=user)

        use_case = make_authenticate_user_usecase(session)

        input_dto = AuthenticateUserInputDTO(email=email_in, password="wrong password")

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(input_dto)
