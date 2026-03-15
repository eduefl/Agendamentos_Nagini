import pytest
from uuid import uuid4

from domain.user.user_exceptions import UserNotFoundError
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.update_user.update_user_dto import UpdateUserInputDTO
from usecases.user.update_user.update_user_usecase import updateUserUsecase


class TestUpdateUserUseCaseIntegration:
    def test_update_user_usecase(self, tst_db_session, make_user):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)

        user = make_user(name="John Doe")
        user_repo.add_user(user=user)

        use_case = updateUserUsecase(user_repo)
        input_dto = UpdateUserInputDTO(id=user.id, name="Jane Doe")

        # Act
        output = use_case.execute(input_dto)

        # Assert (retorno)
        assert output.id == user.id
        assert output.name == "Jane Doe"

        # Assert (persistência no banco)
        updated_user = user_repo.find_user_by_id(user_id=user.id)
        assert updated_user.id == user.id
        assert updated_user.name == "Jane Doe"

    def test_update_user_usecase_user_not_found(self, tst_db_session):
        # Arrange
        session = tst_db_session
        user_repo = userRepository(session=session)

        use_case = updateUserUsecase(user_repo)
        input_dto = UpdateUserInputDTO(id=uuid4(), name="Jane Doe")

        # Act / Assert
        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)


