import pytest
from uuid import uuid4

from domain.user.user_exceptions import UserNotFoundError
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdInputDTO
from usecases.user.find_user_by_id.find_user_by_id_usecase import FindUserByIdUseCase


class TestFindUserByIdUseCaseIntegration:
    def test_find_user_by_id(self, tst_db_session, make_user, seed_roles):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)

        user = make_user(
            name="John Doe",
            email="john.doe@example.com",
            is_active=True,
            roles={"cliente"},
        )
        user_repo.add_user(user=user)

        use_case = FindUserByIdUseCase(user_repo)
        input_dto = findUserByIdInputDTO(id=user.id)

        # Act
        output = use_case.execute(input=input_dto)

        # Assert
        assert output.id == user.id
        assert output.name == "John Doe"
        assert str(output.email) == "john.doe@example.com"
        assert output.is_active is True
        assert output.roles == ["cliente"]


    def test_find_user_by_id_raises_when_user_not_found(self, tst_db_session):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)

        use_case = FindUserByIdUseCase(user_repo)
        input_dto = findUserByIdInputDTO(id=uuid4())

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            use_case.execute(input=input_dto)

    def test_find_user_by_id_returns_inactive_user(self, tst_db_session, make_user, seed_roles):
        session = tst_db_session
        user_repo = userRepository(session=session)

        user = make_user(
            name="John Doe",
            email="john.doe@example.com",
            is_active=False,
            roles={"cliente"},
        )
        user_repo.add_user(user=user)

        use_case = FindUserByIdUseCase(user_repo)
        input_dto = findUserByIdInputDTO(id=user.id)

        output = use_case.execute(input=input_dto)

        assert output.id == user.id
        assert output.is_active is False
        assert output.roles == ["cliente"]