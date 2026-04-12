"""
Testes que cobrem as linhas `raise NotImplementedError` dos métodos abstratos
de todas as interfaces do domínio.

A estratégia é criar uma subclasse concreta que chama `super().método()` para
cada método abstrato, de forma que o corpo da implementação padrão (que contém
`raise NotImplementedError`) seja executado e coberto.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4, UUID

# ─── UseCaseInterface ────────────────────────────────────────────────────────

from domain.__seedwork.use_case_interface import UseCaseInterface


class _ConcreteUseCase(UseCaseInterface):
    def execute(input_data=None):
        return super(_ConcreteUseCase, _ConcreteUseCase).execute(input_data)


def test_use_case_interface_execute_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        _ConcreteUseCase.execute(None)


# ─── LogisticsAclGatewayInterface ────────────────────────────────────────────

from domain.logistics.logistics_acl_gateway_interface import LogisticsAclGatewayInterface


class _ConcreteLogisticsGateway(LogisticsAclGatewayInterface):
    def estimate_route(self, origin_address, destination_address, departure_at):
        return super().estimate_route(origin_address, destination_address, departure_at)


def test_logistics_gateway_estimate_route_raises_not_implemented():
    obj = _ConcreteLogisticsGateway()
    with pytest.raises(NotImplementedError):
        obj.estimate_route("A", "B", datetime.utcnow())


# ─── EmailSenderInterface ─────────────────────────────────────────────────────

from domain.notification.email_sender_interface import EmailSenderInterface


class _ConcreteEmailSender(EmailSenderInterface):
    def send_activation_email(self, to_email, activation_code):
        return super().send_activation_email(to_email, activation_code)

    def send_service_request_notification_email(
        self, to_email, provider_name, service_name, desired_datetime, address, expires_at
    ):
        return super().send_service_request_notification_email(
            to_email, provider_name, service_name, desired_datetime, address, expires_at
        )

    def send_service_request_confirmed_to_client(
        self, client_email, client_name, service_name, service_price, travel_price, total_price, status
    ):
        return super().send_service_request_confirmed_to_client(
            client_email, client_name, service_name, service_price, travel_price, total_price, status
        )

    def send_service_request_confirmed_to_provider(
        self, provider_email, provider_name, service_name, service_price, service_address, travel_price, total_price
    ):
        return super().send_service_request_confirmed_to_provider(
            provider_email, provider_name, service_name, service_price, service_address, travel_price, total_price
        )

    def send_travel_started_to_client(
        self, client_email, client_name, estimated_arrival_at, travel_duration_minutes
    ):
        return super().send_travel_started_to_client(
            client_email, client_name, estimated_arrival_at, travel_duration_minutes
        )

    def send_provider_arrived_to_client(self, client_email, client_name, provider_arrived_at):
        return super().send_provider_arrived_to_client(client_email, client_name, provider_arrived_at)

    def send_payment_requested_to_client(self, client_email, client_name, payment_amount, payment_requested_at):
        return super().send_payment_requested_to_client(
            client_email, client_name, payment_amount, payment_requested_at
        )

    def send_payment_approved_to_client(self, client_email, client_name, payment_amount, payment_approved_at):
        return super().send_payment_approved_to_client(
            client_email, client_name, payment_amount, payment_approved_at
        )

    def send_payment_approved_to_provider(self, provider_email, provider_name, payment_amount, payment_approved_at):
        return super().send_payment_approved_to_provider(
            provider_email, provider_name, payment_amount, payment_approved_at
        )

    def send_payment_refused_to_client(
        self, client_email, client_name, payment_amount, payment_refused_at, refusal_reason=None
    ):
        return super().send_payment_refused_to_client(
            client_email, client_name, payment_amount, payment_refused_at, refusal_reason
        )

    def send_payment_refused_to_provider(self, provider_email, provider_name, payment_amount, payment_refused_at):
        return super().send_payment_refused_to_provider(
            provider_email, provider_name, payment_amount, payment_refused_at
        )


class TestEmailSenderInterface:
    def setup_method(self):
        self.sender = _ConcreteEmailSender()
        self.now = datetime.utcnow()
        self.amount = Decimal("100.00")

    def test_send_activation_email_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_activation_email("a@b.com", "123")

    def test_send_service_request_notification_email_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_service_request_notification_email(
                "a@b.com", "Prov", "Serv", self.now, "Addr", self.now
            )

    def test_send_service_request_confirmed_to_client_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_service_request_confirmed_to_client(
                "c@b.com", "Client", "Serv",
                self.amount, self.amount, self.amount, "CONFIRMED"
            )

    def test_send_service_request_confirmed_to_provider_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_service_request_confirmed_to_provider(
                "p@b.com", "Prov", "Serv",
                self.amount, "Addr", self.amount, self.amount
            )

    def test_send_travel_started_to_client_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_travel_started_to_client("c@b.com", "Client", self.now, 30)

    def test_send_provider_arrived_to_client_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_provider_arrived_to_client("c@b.com", "Client", self.now)

    def test_send_payment_requested_to_client_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_payment_requested_to_client("c@b.com", "Client", self.amount, self.now)

    def test_send_payment_approved_to_client_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_payment_approved_to_client("c@b.com", "Client", self.amount, self.now)

    def test_send_payment_approved_to_provider_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_payment_approved_to_provider("p@b.com", "Prov", self.amount, self.now)

    def test_send_payment_refused_to_client_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_payment_refused_to_client("c@b.com", "Client", self.amount, self.now)

    def test_send_payment_refused_to_provider_raises(self):
        with pytest.raises(NotImplementedError):
            self.sender.send_payment_refused_to_provider("p@b.com", "Prov", self.amount, self.now)


# ─── ServiceRequestNotificationGatewayInterface ──────────────────────────────

from domain.notification.notification_gateway_interface import (
    ServiceRequestNotificationGatewayInterface,
)


class _ConcreteNotificationGateway(ServiceRequestNotificationGatewayInterface):
    def notify_client_travel_started(self, client_id, service_request_id, estimated_arrival_at, travel_duration_minutes):
        return super().notify_client_travel_started(
            client_id, service_request_id, estimated_arrival_at, travel_duration_minutes
        )

    def notify_client_provider_arrived(self, client_id, service_request_id, provider_arrived_at):
        return super().notify_client_provider_arrived(client_id, service_request_id, provider_arrived_at)

    def notify_payment_requested(self, client_id, service_request_id, payment_amount, payment_requested_at):
        return super().notify_payment_requested(
            client_id, service_request_id, payment_amount, payment_requested_at
        )

    def notify_payment_approved(self, client_id, provider_id, service_request_id, payment_amount, payment_approved_at):
        return super().notify_payment_approved(
            client_id, provider_id, service_request_id, payment_amount, payment_approved_at
        )

    def notify_payment_refused(
        self, client_id, provider_id, service_request_id, payment_amount, payment_refused_at, refusal_reason=None
    ):
        return super().notify_payment_refused(
            client_id, provider_id, service_request_id, payment_amount, payment_refused_at, refusal_reason
        )


class TestNotificationGatewayInterface:
    def setup_method(self):
        self.gw = _ConcreteNotificationGateway()
        self.now = datetime.utcnow()
        self.uid = uuid4()
        self.amount = Decimal("50.00")

    def test_notify_client_travel_started_raises(self):
        with pytest.raises(NotImplementedError):
            self.gw.notify_client_travel_started(self.uid, self.uid, self.now, 20)

    def test_notify_client_provider_arrived_raises(self):
        with pytest.raises(NotImplementedError):
            self.gw.notify_client_provider_arrived(self.uid, self.uid, self.now)

    def test_notify_payment_requested_raises(self):
        with pytest.raises(NotImplementedError):
            self.gw.notify_payment_requested(self.uid, self.uid, self.amount, self.now)

    def test_notify_payment_approved_raises(self):
        with pytest.raises(NotImplementedError):
            self.gw.notify_payment_approved(self.uid, self.uid, self.uid, self.amount, self.now)

    def test_notify_payment_refused_raises(self):
        with pytest.raises(NotImplementedError):
            self.gw.notify_payment_refused(self.uid, self.uid, self.uid, self.amount, self.now)


# ─── PaymentAclGatewayInterface ──────────────────────────────────────────────

from domain.payment.payment_acl_gateway_interface import PaymentAclGatewayInterface


class _ConcretePaymentGateway(PaymentAclGatewayInterface):
    def process_payment(self, external_reference, amount, payer_id, service_request_id, requested_at):
        return super().process_payment(external_reference, amount, payer_id, service_request_id, requested_at)


def test_payment_gateway_process_payment_raises():
    obj = _ConcretePaymentGateway()
    with pytest.raises(NotImplementedError):
        obj.process_payment("ref", Decimal("100"), uuid4(), uuid4(), datetime.utcnow())


# ─── PaymentAttemptRepositoryInterface ───────────────────────────────────────

from domain.payment.payment_attempt_repository_interface import PaymentAttemptRepositoryInterface
from domain.payment.payment_attempt_entity import PaymentAttempt


class _ConcretePaymentAttemptRepo(PaymentAttemptRepositoryInterface):
    def create(self, attempt):
        return super().create(attempt)

    def find_latest_by_service_request_id(self, service_request_id):
        return super().find_latest_by_service_request_id(service_request_id)

    def find_by_external_reference(self, external_reference):
        return super().find_by_external_reference(external_reference)

    def mark_processing(self, attempt_id):
        return super().mark_processing(attempt_id)

    def mark_approved(self, attempt_id):
        return super().mark_approved(attempt_id)

    def mark_refused(self, attempt_id, refusal_reason=None):
        return super().mark_refused(attempt_id, refusal_reason)

    def count_by_service_request_id(self, service_request_id):
        return super().count_by_service_request_id(service_request_id)

    def record_gateway_reference(self, attempt_id, provider, external_reference, provider_message=None):
        return super().record_gateway_reference(attempt_id, provider, external_reference, provider_message)


class TestPaymentAttemptRepositoryInterface:
    def setup_method(self):
        self.repo = _ConcretePaymentAttemptRepo()
        self.uid = uuid4()

    def test_create_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.create(None)

    def test_find_latest_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_latest_by_service_request_id(self.uid)

    def test_find_by_external_reference_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_by_external_reference("ext-ref")

    def test_mark_processing_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_processing(self.uid)

    def test_mark_approved_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_approved(self.uid)

    def test_mark_refused_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_refused(self.uid)

    def test_count_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.count_by_service_request_id(self.uid)

    def test_record_gateway_reference_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.record_gateway_reference(self.uid, "prov", "ext-ref")


# ─── PasswordHasherInterface ──────────────────────────────────────────────────

from domain.security.password_hasher_interface import PasswordHasherInterface


class _ConcretePasswordHasher(PasswordHasherInterface):
    def hash(self, password):
        return super().hash(password)

    def verify(self, password, hashed_password):
        return super().verify(password, hashed_password)


def test_password_hasher_hash_raises():
    with pytest.raises(NotImplementedError):
        _ConcretePasswordHasher().hash("secret")


def test_password_hasher_verify_raises():
    with pytest.raises(NotImplementedError):
        _ConcretePasswordHasher().verify("secret", "hashed")


# ─── TokenServiceInterface ────────────────────────────────────────────────────

from domain.security.token_service_interface import TokenServiceInterface


class _ConcreteTokenService(TokenServiceInterface):
    def create_access_token(self, data):
        return super().create_access_token(data)

    def decode_token(self, token):
        return super().decode_token(token)


def test_token_service_create_raises():
    with pytest.raises(NotImplementedError):
        _ConcreteTokenService().create_access_token(None)


def test_token_service_decode_raises():
    with pytest.raises(NotImplementedError):
        _ConcreteTokenService().decode_token("token")


# ─── ProviderServiceRepositoryInterface ──────────────────────────────────────

from domain.service.provider_service_repository_interface import ProviderServiceRepositoryInterface


class _ConcreteProviderServiceRepo(ProviderServiceRepositoryInterface):
    def create_provider_service(self, provider_service):
        return super().create_provider_service(provider_service)

    def find_by_provider_and_service(self, provider_id, service_id):
        return super().find_by_provider_and_service(provider_id, service_id)

    def find_by_id(self, provider_service_id):
        return super().find_by_id(provider_service_id)

    def update(self, provider_service):
        return super().update(provider_service)

    def list_by_provider_id(self, provider_id):
        return super().list_by_provider_id(provider_id)

    def list_eligible_providers_by_service_id(self, service_id):
        return super().list_eligible_providers_by_service_id(service_id)

    def find_active_by_provider_and_service(self, provider_id, service_id):
        return super().find_active_by_provider_and_service(provider_id, service_id)


class TestProviderServiceRepositoryInterface:
    def setup_method(self):
        self.repo = _ConcreteProviderServiceRepo()
        self.uid = uuid4()

    def test_create_provider_service_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.create_provider_service(None)

    def test_find_by_provider_and_service_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_by_provider_and_service(self.uid, self.uid)

    def test_find_by_id_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_by_id(self.uid)

    def test_update_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.update(None)

    def test_list_by_provider_id_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_by_provider_id(self.uid)

    def test_list_eligible_providers_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_eligible_providers_by_service_id(self.uid)

    def test_find_active_by_provider_and_service_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_active_by_provider_and_service(self.uid, self.uid)


# ─── ServiceRepositoryInterface ──────────────────────────────────────────────

from domain.service.service_repository_interface import ServiceRepositoryInterface


class _ConcreteServiceRepo(ServiceRepositoryInterface):
    def create_service(self, service):
        return super().create_service(service)

    def find_by_id(self, service_id):
        return super().find_by_id(service_id)

    def find_by_name(self, name):
        return super().find_by_name(name)

    def list_all(self):
        return super().list_all()


class TestServiceRepositoryInterface:
    def setup_method(self):
        self.repo = _ConcreteServiceRepo()
        self.uid = uuid4()

    def test_create_service_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.create_service(None)

    def test_find_by_id_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_by_id(self.uid)

    def test_find_by_name_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_by_name("Serviço")

    def test_list_all_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_all()


# ─── ServiceRequestRepositoryInterface ───────────────────────────────────────

from domain.service_request.service_request_repository_interface import ServiceRequestRepositoryInterface


class _ConcreteServiceRequestRepo(ServiceRequestRepositoryInterface):
    def create(self, service_request):
        return super().create(service_request)

    def find_by_id(self, service_request_id):
        return super().find_by_id(service_request_id)

    def list_by_client_id(self, client_id):
        return super().list_by_client_id(client_id)

    def list_by_client_id_with_service_data(self, client_id):
        return super().list_by_client_id_with_service_data(client_id)

    def update(self, service_request):
        return super().update(service_request)

    def list_available_for_provider(self, provider_id):
        return super().list_available_for_provider(provider_id)

    def confirm_if_available(self, service_request_id, accepted_provider_id, departure_address,
                              service_price, travel_price, total_price, accepted_at):
        return super().confirm_if_available(service_request_id, accepted_provider_id, departure_address,
                                             service_price, travel_price, total_price, accepted_at)

    def list_operational_schedule_for_provider(self, provider_id, start=None, end=None):
        return super().list_operational_schedule_for_provider(provider_id, start, end)

    def start_travel_if_confirmed(self, service_request_id, provider_id, now,
                                   estimated_arrival_at, travel_duration_minutes,
                                   travel_distance_km, logistics_reference):
        return super().start_travel_if_confirmed(service_request_id, provider_id, now,
                                                  estimated_arrival_at, travel_duration_minutes,
                                                  travel_distance_km, logistics_reference)

    def mark_arrived_if_in_transit(self, service_request_id, provider_id, now):
        return super().mark_arrived_if_in_transit(service_request_id, provider_id, now)

    def confirm_provider_arrival_and_start_service_if_arrived(self, service_request_id, client_id, now):
        return super().confirm_provider_arrival_and_start_service_if_arrived(service_request_id, client_id, now)

    def finish_service_if_in_progress(self, service_request_id, provider_id, now):
        return super().finish_service_if_in_progress(service_request_id, provider_id, now)

    def start_payment_processing_if_awaiting_payment(self, service_request_id, client_id, now, payment_reference=None):
        return super().start_payment_processing_if_awaiting_payment(
            service_request_id, client_id, now, payment_reference
        )

    def start_payment_processing_and_mark_attempt_if_awaiting_payment(
        self, service_request_id, client_id, attempt_id, now
    ):
        return super().start_payment_processing_and_mark_attempt_if_awaiting_payment(
            service_request_id, client_id, attempt_id, now
        )

    def mark_payment_approved_if_processing(self, service_request_id, now):
        return super().mark_payment_approved_if_processing(service_request_id, now)

    def mark_payment_refused_if_processing(self, service_request_id, now):
        return super().mark_payment_refused_if_processing(service_request_id, now)

    def mark_payment_approved_and_complete_service_if_processing(
        self, service_request_id, attempt_id, provider, external_reference, provider_message, processed_at
    ):
        return super().mark_payment_approved_and_complete_service_if_processing(
            service_request_id, attempt_id, provider, external_reference, provider_message, processed_at
        )

    def mark_payment_refused_and_reopen_for_payment_if_processing(
        self, service_request_id, attempt_id, provider, external_reference,
        refusal_reason, provider_message, processed_at
    ):
        return super().mark_payment_refused_and_reopen_for_payment_if_processing(
            service_request_id, attempt_id, provider, external_reference,
            refusal_reason, provider_message, processed_at
        )

    def finish_service_and_open_payment_if_in_progress(
        self, service_request_id, provider_id, now, payment_amount, payment_attempt_id
    ):
        return super().finish_service_and_open_payment_if_in_progress(
            service_request_id, provider_id, now, payment_amount, payment_attempt_id
        )


class TestServiceRequestRepositoryInterface:
    def setup_method(self):
        self.repo = _ConcreteServiceRequestRepo()
        self.uid = uuid4()
        self.now = datetime.utcnow()

    def test_create_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.create(None)

    def test_find_by_id_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_by_id(self.uid)

    def test_list_by_client_id_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_by_client_id(self.uid)

    def test_list_by_client_id_with_service_data_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_by_client_id_with_service_data(self.uid)

    def test_update_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.update(None)

    def test_list_available_for_provider_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_available_for_provider(self.uid)

    def test_confirm_if_available_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.confirm_if_available(
                self.uid, self.uid, "Addr",
                Decimal("100"), Decimal("20"), Decimal("120"), self.now
            )

    def test_list_operational_schedule_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_operational_schedule_for_provider(self.uid)

    def test_start_travel_if_confirmed_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.start_travel_if_confirmed(
                self.uid, self.uid, self.now, self.now, 30, None, None
            )

    def test_mark_arrived_if_in_transit_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_arrived_if_in_transit(self.uid, self.uid, self.now)

    def test_confirm_provider_arrival_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.confirm_provider_arrival_and_start_service_if_arrived(self.uid, self.uid, self.now)

    def test_finish_service_if_in_progress_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.finish_service_if_in_progress(self.uid, self.uid, self.now)

    def test_start_payment_processing_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.start_payment_processing_if_awaiting_payment(self.uid, self.uid, self.now)

    def test_start_payment_processing_and_mark_attempt_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.start_payment_processing_and_mark_attempt_if_awaiting_payment(
                self.uid, self.uid, self.uid, self.now
            )

    def test_mark_payment_approved_if_processing_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_payment_approved_if_processing(self.uid, self.now)

    def test_mark_payment_refused_if_processing_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_payment_refused_if_processing(self.uid, self.now)

    def test_mark_payment_approved_and_complete_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_payment_approved_and_complete_service_if_processing(
                self.uid, self.uid, "prov", "ext-ref", None, self.now
            )

    def test_mark_payment_refused_and_reopen_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.mark_payment_refused_and_reopen_for_payment_if_processing(
                self.uid, self.uid, "prov", "ext-ref", None, None, self.now
            )

    def test_finish_service_and_open_payment_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.finish_service_and_open_payment_if_in_progress(
                self.uid, self.uid, self.now, Decimal("200"), self.uid
            )


# ─── TravelPriceGatewayInterface ──────────────────────────────────────────────

from domain.travel.travel_price_gateway_interface import TravelPriceGatewayInterface


class _ConcreteTravelPriceGateway(TravelPriceGatewayInterface):
    def calculate_price(self, departure_address, destination_address):
        return super().calculate_price(departure_address, destination_address)


def test_travel_price_gateway_raises():
    with pytest.raises(NotImplementedError):
        _ConcreteTravelPriceGateway().calculate_price("A", "B")


# ─── userRepositoryInterface ──────────────────────────────────────────────────

from domain.user.user_repository_interface import userRepositoryInterface


class _ConcreteUserRepo(userRepositoryInterface):
    def add_user(self, user):
        return super().add_user(user)

    def find_user_by_id(self, user_id):
        return super().find_user_by_id(user_id)

    def find_user_by_email(self, email):
        return super().find_user_by_email(email)

    def update_user(self, user):
        return super().update_user(user)

    def list_users(self):
        return super().list_users()

    def add_role_to_user(self, user_id, role_name):
        return super().add_role_to_user(user_id, role_name)

    def remove_role_from_user(self, user_id, role_name):
        return super().remove_role_from_user(user_id, role_name)

    def list_user_roles(self, user_id):
        return super().list_user_roles(user_id)


class TestUserRepositoryInterface:
    def setup_method(self):
        self.repo = _ConcreteUserRepo()
        self.uid = uuid4()

    def test_add_user_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.add_user(None)

    def test_find_user_by_id_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_user_by_id(self.uid)

    def test_find_user_by_email_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.find_user_by_email("a@b.com")

    def test_update_user_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.update_user(None)

    def test_list_users_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_users()

    def test_add_role_to_user_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.add_role_to_user(self.uid, "cliente")

    def test_remove_role_from_user_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.remove_role_from_user(self.uid, "cliente")

    def test_list_user_roles_raises(self):
        with pytest.raises(NotImplementedError):
            self.repo.list_user_roles(self.uid)