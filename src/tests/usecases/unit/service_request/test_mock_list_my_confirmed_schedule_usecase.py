from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.__seedwork.exceptions import ForbiddenError, ValidationError
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.user.user_exceptions import UserNotFoundError
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service_request.list_my_confirmed_schedule.list_my_confirmed_schedule_dto import (
    ListMyConfirmedScheduleInputDTO,
    ListMyConfirmedScheduleOutputItemDTO,
)
from usecases.service_request.list_my_confirmed_schedule.list_my_confirmed_schedule_usecase import (
    ListMyConfirmedScheduleUseCase,
)


def _make_schedule_item(**overrides):
    provider_id = overrides.pop("provider_id", uuid4())
    data = {
        "service_request_id": uuid4(),
        "provider_id": provider_id,
        "client_id": uuid4(),
        "service_id": uuid4(),
        "service_name": "Instalação",
        "service_description": "Instalação técnica",
        "desired_datetime": datetime(2026, 4, 7, 14, 0, 0),
        "address": "Rua X, 123",
        "status": "CONFIRMED",
        "service_price": Decimal("100.00"),
        "travel_price": Decimal("25.00"),
        "total_price": Decimal("125.00"),
        "accepted_at": datetime(2026, 4, 5, 11, 30, 0),
    }
    data.update(overrides)
    return MagicMock(**data)


class TestListMyConfirmedScheduleUseCase:
    def _make_use_case(self):
        mock_sr_repo = MagicMock(spec=ServiceRequestRepositoryInterface)
        mock_user_repo = MagicMock(spec=userRepositoryInterface)
        use_case = ListMyConfirmedScheduleUseCase(
            service_request_repository=mock_sr_repo,
            user_repository=mock_user_repo,
        )
        return use_case, mock_sr_repo, mock_user_repo

    def _make_active_provider(self, provider_id=None):
        provider_id = provider_id or uuid4()
        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = True
        return mock_user

    def test_success_returns_confirmed_items(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user_repo.find_user_by_id.return_value = self._make_active_provider(provider_id)

        item = _make_schedule_item(provider_id=provider_id)
        mock_sr_repo.list_confirmed_schedule_for_provider.return_value = [item]

        input_dto = ListMyConfirmedScheduleInputDTO(provider_id=provider_id)
        output = use_case.execute(input_dto)

        assert len(output) == 1
        assert isinstance(output[0], ListMyConfirmedScheduleOutputItemDTO)
        assert output[0].status == "CONFIRMED"
        mock_user_repo.find_user_by_id.assert_called_once_with(provider_id)
        mock_sr_repo.list_confirmed_schedule_for_provider.assert_called_once_with(
            provider_id=provider_id,
            start=None,
            end=None,
        )

    def test_success_empty_list(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user_repo.find_user_by_id.return_value = self._make_active_provider(provider_id)
        mock_sr_repo.list_confirmed_schedule_for_provider.return_value = []

        input_dto = ListMyConfirmedScheduleInputDTO(provider_id=provider_id)
        output = use_case.execute(input_dto)

        assert output == []

    def test_success_passes_start_and_end_to_repository(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user_repo.find_user_by_id.return_value = self._make_active_provider(provider_id)
        mock_sr_repo.list_confirmed_schedule_for_provider.return_value = []

        start = datetime(2026, 4, 1, 0, 0, 0)
        end = datetime(2026, 4, 30, 23, 59, 59)
        input_dto = ListMyConfirmedScheduleInputDTO(provider_id=provider_id, start=start, end=end)
        use_case.execute(input_dto)

        mock_sr_repo.list_confirmed_schedule_for_provider.assert_called_once_with(
            provider_id=provider_id,
            start=start,
            end=end,
        )

    def test_inactive_user_raises_forbidden(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user = MagicMock(id=provider_id, is_active=False)
        mock_user_repo.find_user_by_id.return_value = mock_user

        input_dto = ListMyConfirmedScheduleInputDTO(provider_id=provider_id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_sr_repo.list_confirmed_schedule_for_provider.assert_not_called()

    def test_non_provider_user_raises_forbidden(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user = MagicMock(id=provider_id, is_active=True)
        mock_user.is_provider.return_value = False
        mock_user_repo.find_user_by_id.return_value = mock_user

        input_dto = ListMyConfirmedScheduleInputDTO(provider_id=provider_id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)

        mock_sr_repo.list_confirmed_schedule_for_provider.assert_not_called()

    def test_user_not_found_raises_error(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user_repo.find_user_by_id.side_effect = UserNotFoundError(provider_id)

        input_dto = ListMyConfirmedScheduleInputDTO(provider_id=provider_id)

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)

        mock_sr_repo.list_confirmed_schedule_for_provider.assert_not_called()

    def test_invalid_period_start_greater_than_end_raises_validation_error(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user_repo.find_user_by_id.return_value = self._make_active_provider(provider_id)

        input_dto = ListMyConfirmedScheduleInputDTO(
            provider_id=provider_id,
            start=datetime(2026, 4, 30, 0, 0, 0),
            end=datetime(2026, 4, 1, 0, 0, 0),
        )

        with pytest.raises(ValidationError, match="start deve ser menor ou igual a end"):
            use_case.execute(input_dto)

        mock_sr_repo.list_confirmed_schedule_for_provider.assert_not_called()

    def test_equal_start_and_end_is_valid(self):
        use_case, mock_sr_repo, mock_user_repo = self._make_use_case()
        provider_id = uuid4()
        mock_user_repo.find_user_by_id.return_value = self._make_active_provider(provider_id)
        mock_sr_repo.list_confirmed_schedule_for_provider.return_value = []

        dt = datetime(2026, 4, 15, 12, 0, 0)
        input_dto = ListMyConfirmedScheduleInputDTO(provider_id=provider_id, start=dt, end=dt)
        output = use_case.execute(input_dto)
        assert output == []