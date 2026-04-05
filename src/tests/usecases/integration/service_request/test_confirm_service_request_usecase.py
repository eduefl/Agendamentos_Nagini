from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy.orm import sessionmaker

import pytest

from domain.service_request.service_request_entity import (
    ServiceRequest,
    ServiceRequestStatus,
)
from domain.service_request.service_request_exceptions import (
    ProviderDoesNotServeThisRequestError,
    ServiceRequestNotFoundError,
    ServiceRequestUnavailableError,
)
from domain.travel.travel_price_gateway_interface import TravelPriceGatewayInterface
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)
from infrastructure.service.sqlalchemy.provider_service_repository import (
    ProviderServiceRepository,
)
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)
from infrastructure.service_request.sqlalchemy.service_request_repository import (
    ServiceRequestRepository,
)
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.service_request.confirm_service_request.confirm_service_request_dto import (
    ConfirmServiceRequestInputDTO,
    ConfirmServiceRequestOutputDTO,
)
from usecases.service_request.confirm_service_request.confirm_service_request_usecase import (
    ConfirmServiceRequestUseCase,
)


class DeterministicTravelPriceGateway(TravelPriceGatewayInterface):
    def __init__(self, fixed_price: Decimal):
        self.fixed_price = fixed_price

    def calculate_price(
        self,
        departure_address: str,
        destination_address: str,
    ) -> Decimal:
        return self.fixed_price

class BarrierTravelPriceGateway(TravelPriceGatewayInterface):
    def __init__(self, barrier: Barrier, fixed_price: Decimal):
        self._barrier = barrier
        self._fixed_price = fixed_price

    def calculate_price(
        self,
        departure_address: str,
        destination_address: str,
    ) -> Decimal:
        self._barrier.wait(timeout=5)
        return self._fixed_price


class TestConfirmServiceRequestUseCaseIntegration:
    @staticmethod
    def _create_user(session, make_user, roles, email=None, name=None):
        repo = userRepository(session=session)
        user = make_user(
            id=uuid4(),
            name=name or f"User {uuid4().hex[:8]}",
            email=email or f"{uuid4().hex}@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles=roles,
        )
        repo.add_user(user)
        return user

    @staticmethod
    def _create_service(session, name=None):
        service = ServiceModel(
            id=uuid4(),
            name=name or f"Servico {uuid4().hex}",
            description="Descricao",
        )
        session.add(service)
        session.commit()
        return service

    @staticmethod
    def _create_provider_service(
        session,
        provider_id,
        service_id,
        price=Decimal("100.00"),
        active=True,
    ):
        provider_service = ProviderServiceModel(
            id=uuid4(),
            provider_id=provider_id,
            service_id=service_id,
            price=price,
            active=active,
        )
        session.add(provider_service)
        session.commit()
        return provider_service

    @staticmethod
    def _create_service_request(
        session,
        client_id,
        service_id,
        status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
        expires_delta=timedelta(hours=1),
        address="Rua Destino, 100",
    ):
        repo = ServiceRequestRepository(session=session)
        sr = ServiceRequest(
            id=uuid4(),
            client_id=client_id,
            service_id=service_id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address=address,
            status=status,
            expires_at=datetime.utcnow() + expires_delta,
        )
        return repo.create(sr)

    @staticmethod
    def _make_use_case(session, travel_price=Decimal("25.00")):
        service_request_repository = ServiceRequestRepository(session=session)
        provider_service_repository = ProviderServiceRepository(session=session)
        travel_gateway = DeterministicTravelPriceGateway(fixed_price=travel_price)

        return (
            ConfirmServiceRequestUseCase(
                service_request_repository=service_request_repository,
                provider_service_repository=provider_service_repository,
                travel_price_gateway=travel_gateway,
            ),
            service_request_repository,
        )

    def test_confirm_service_request_success(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"}, name="Cliente")
        provider = self._create_user(
            session, make_user, {"prestador"}, name="Prestador"
        )
        service = self._create_service(session, name="Depilacao")

        self._create_provider_service(
            session=session,
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("100.00"),
            active=True,
        )

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_delta=timedelta(hours=1),
            address="Rua Destino, 100",
        )

        use_case, service_request_repository = self._make_use_case(
            session=session,
            travel_price=Decimal("25.00"),
        )

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider.id,
            departure_address="Rua Saida, 123",
        )

        output = use_case.execute(input_dto)

        assert isinstance(output, ConfirmServiceRequestOutputDTO)
        assert output.service_request_id == service_request.id
        assert output.status == ServiceRequestStatus.CONFIRMED.value
        assert output.accepted_provider_id == provider.id
        assert output.service_price == Decimal("100.00")
        assert output.travel_price == Decimal("25.00")
        assert output.total_price == Decimal("125.00")
        assert output.accepted_at is not None

        persisted = service_request_repository.find_by_id(output.service_request_id)
        assert persisted is not None
        assert persisted.status == ServiceRequestStatus.CONFIRMED.value
        assert persisted.accepted_provider_id == provider.id
        assert persisted.departure_address == "Rua Saida, 123"
        assert persisted.service_price == Decimal("100.00")
        assert persisted.travel_price == Decimal("25.00")
        assert persisted.total_price == Decimal("125.00")
        assert persisted.accepted_at is not None

    def test_confirm_service_request_not_found(
        self,
        tst_db_session,
    ):
        session = tst_db_session
        use_case, _ = self._make_use_case(session=session)

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=uuid4(),
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ServiceRequestNotFoundError):
            use_case.execute(input_dto)

    def test_confirm_service_request_fails_if_request_not_awaiting_acceptance(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"})
        service = self._create_service(session)

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
        )

        session.query(ServiceRequestModel).filter(
            ServiceRequestModel.id == service_request.id
        ).update({"status": ServiceRequestStatus.CANCELLED.value})
        session.commit()

        use_case, _ = self._make_use_case(session=session)

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ServiceRequestUnavailableError):
            use_case.execute(input_dto)

    def test_confirm_service_request_fails_if_request_expired(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"})
        service = self._create_service(session)

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_delta=timedelta(minutes=-5),
        )

        use_case, _ = self._make_use_case(session=session)

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=uuid4(),
            departure_address="Rua A, 1",
        )

        with pytest.raises(ServiceRequestUnavailableError):
            use_case.execute(input_dto)

    def test_confirm_service_request_fails_if_provider_does_not_serve_service(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})
        service = self._create_service(session)

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
        )

        use_case, _ = self._make_use_case(session=session)

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider.id,
            departure_address="Rua A, 1",
        )

        with pytest.raises(ProviderDoesNotServeThisRequestError):
            use_case.execute(input_dto)

    def test_confirm_service_request_fails_if_another_provider_already_accepted(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"})
        provider_1 = self._create_user(
            session, make_user, {"prestador"}, name="Prestador 1"
        )
        provider_2 = self._create_user(
            session, make_user, {"prestador"}, name="Prestador 2"
        )
        service = self._create_service(session)

        self._create_provider_service(
            session=session,
            provider_id=provider_1.id,
            service_id=service.id,
            price=Decimal("100.00"),
            active=True,
        )
        self._create_provider_service(
            session=session,
            provider_id=provider_2.id,
            service_id=service.id,
            price=Decimal("90.00"),
            active=True,
        )

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
        )

        use_case_1, _ = self._make_use_case(
            session=session, travel_price=Decimal("10.00")
        )
        use_case_2, _ = self._make_use_case(
            session=session, travel_price=Decimal("15.00")
        )

        first_input = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider_1.id,
            departure_address="Rua A, 1",
        )
        second_input = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider_2.id,
            departure_address="Rua B, 2",
        )

        first_output = use_case_1.execute(first_input)

        assert first_output.status == ServiceRequestStatus.CONFIRMED.value
        assert first_output.accepted_provider_id == provider_1.id

        with pytest.raises(ServiceRequestUnavailableError):
            use_case_2.execute(second_input)

    def test_confirm_service_request_persists_prices_correctly(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})
        service = self._create_service(session)

        self._create_provider_service(
            session=session,
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("150.00"),
            active=True,
        )

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
            address="Rua Destino, 999",
        )

        use_case, service_request_repository = self._make_use_case(
            session=session,
            travel_price=Decimal("30.00"),
        )

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider.id,
            departure_address="Rua Saida, 100",
        )

        output = use_case.execute(input_dto)

        assert output.service_price == Decimal("150.00")
        assert output.travel_price == Decimal("30.00")
        assert output.total_price == Decimal("180.00")

        persisted = service_request_repository.find_by_id(service_request.id)
        assert persisted is not None
        assert persisted.service_price == Decimal("150.00")
        assert persisted.travel_price == Decimal("30.00")
        assert persisted.total_price == Decimal("180.00")

    def test_confirm_service_request_total_equals_service_plus_travel(
        self,
        tst_db_session,
        make_user,
        seed_roles,
    ):
        session = tst_db_session
        client = self._create_user(session, make_user, {"cliente"})
        provider = self._create_user(session, make_user, {"prestador"})
        service = self._create_service(session)

        self._create_provider_service(
            session=session,
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("200.00"),
            active=True,
        )

        service_request = self._create_service_request(
            session=session,
            client_id=client.id,
            service_id=service.id,
        )

        use_case, _ = self._make_use_case(
            session=session,
            travel_price=Decimal("45.50"),
        )

        input_dto = ConfirmServiceRequestInputDTO(
            service_request_id=service_request.id,
            provider_id=provider.id,
            departure_address="Rua X, 1",
        )

        output = use_case.execute(input_dto)

        assert output.service_price == Decimal("200.00")
        assert output.travel_price == Decimal("45.50")
        assert output.total_price == Decimal("245.50")
        assert output.total_price == output.service_price + output.travel_price


    def test_confirm_service_request_allows_only_one_winner_in_real_race(
        self,
        concurrent_session_factory,
        make_user,
    ):
        # sessão de setup
        setup_session = concurrent_session_factory()

        # se o seu projeto precisa de roles no banco, execute aqui a mesma lógica do seed_roles
        # exemplo:
        # seed_roles_for_session(setup_session)

        client = self._create_user(setup_session, make_user, {"cliente"}, name="Cliente")
        provider_1 = self._create_user(setup_session, make_user, {"prestador"}, name="Prestador 1")
        provider_2 = self._create_user(setup_session, make_user, {"prestador"}, name="Prestador 2")
        service = self._create_service(setup_session, name="Servico Concorrente")

        self._create_provider_service(
            session=setup_session,
            provider_id=provider_1.id,
            service_id=service.id,
            price=Decimal("100.00"),
            active=True,
        )
        self._create_provider_service(
            session=setup_session,
            provider_id=provider_2.id,
            service_id=service.id,
            price=Decimal("100.00"),
            active=True,
        )

        service_request = self._create_service_request(
            session=setup_session,
            client_id=client.id,
            service_id=service.id,
            status=ServiceRequestStatus.AWAITING_PROVIDER_ACCEPTANCE.value,
            expires_delta=timedelta(hours=1),
            address="Rua Destino, 100",
        )

        setup_session.close()

        barrier = Barrier(2)

        def run_accept(provider_id, departure_address):
            local_session = concurrent_session_factory()
            try:
                use_case = ConfirmServiceRequestUseCase(
                    service_request_repository=ServiceRequestRepository(session=local_session),
                    provider_service_repository=ProviderServiceRepository(session=local_session),
                    travel_price_gateway=BarrierTravelPriceGateway(
                        barrier=barrier,
                        fixed_price=Decimal("25.00"),
                    ),
                )

                input_dto = ConfirmServiceRequestInputDTO(
                    service_request_id=service_request.id,
                    provider_id=provider_id,
                    departure_address=departure_address,
                )

                output = use_case.execute(input_dto)
                return ("success", output)

            except Exception as exc:
                return ("error", exc)

            finally:
                local_session.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_1 = executor.submit(run_accept, provider_1.id, "Rua A, 1")
            future_2 = executor.submit(run_accept, provider_2.id, "Rua B, 2")

            result_1 = future_1.result(timeout=10)
            result_2 = future_2.result(timeout=10)

        results = [result_1, result_2]
        successes = [value for kind, value in results if kind == "success"]
        errors = [value for kind, value in results if kind == "error"]

        assert len(successes) == 1, [f"{type(e).__name__}: {e}" for e in errors]
        assert len(errors) == 1, [f"{type(e).__name__}: {e}" for e in errors]
        assert isinstance(errors[0], ServiceRequestUnavailableError)

        winner = successes[0]
        assert winner.status == ServiceRequestStatus.CONFIRMED.value
        assert winner.accepted_provider_id in {provider_1.id, provider_2.id}
        assert winner.service_price == Decimal("100.00")
        assert winner.travel_price == Decimal("25.00")
        assert winner.total_price == Decimal("125.00")

        verification_session = concurrent_session_factory()
        try:
            persisted = ServiceRequestRepository(session=verification_session).find_by_id(
                service_request.id
            )

            assert persisted is not None
            assert persisted.status == ServiceRequestStatus.CONFIRMED.value
            assert persisted.accepted_provider_id == winner.accepted_provider_id
            assert persisted.departure_address in {"Rua A, 1", "Rua B, 2"}
            assert persisted.service_price == Decimal("100.00")
            assert persisted.travel_price == Decimal("25.00")
            assert persisted.total_price == Decimal("125.00")
            assert persisted.accepted_at is not None
        finally:
            verification_session.close()

