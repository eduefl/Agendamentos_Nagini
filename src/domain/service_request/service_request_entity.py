from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Union
from uuid import UUID

from domain.payment.payment_status_snapshot import PaymentStatusSnapshot


class ServiceRequestStatus(str, Enum):
    REQUESTED = "REQUESTED"
    AWAITING_PROVIDER_ACCEPTANCE = "AWAITING_PROVIDER_ACCEPTANCE"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    # Fase 1 — estados operacionais pós-confirmação
    IN_TRANSIT = "IN_TRANSIT"
    IN_PROGRESS = "IN_PROGRESS"
    ARRIVED = "ARRIVED"
    # Fase 1 — estados financeiros pós-serviço
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    COMPLETED = "COMPLETED"


# Conjunto de status que representam o ciclo operacional (pós-confirmação)
_OPERATIONAL_STATUSES = {
    ServiceRequestStatus.CONFIRMED.value,
    ServiceRequestStatus.IN_TRANSIT.value,
    ServiceRequestStatus.IN_PROGRESS.value,
    ServiceRequestStatus.ARRIVED.value,
}

# Conjunto de status que representam o ciclo financeiro pós-serviço
_FINANCIAL_STATUSES = {
    ServiceRequestStatus.AWAITING_PAYMENT.value,
    ServiceRequestStatus.PAYMENT_PROCESSING.value,
    ServiceRequestStatus.COMPLETED.value,
}


class ServiceRequest:
    def __init__(
        self,
        id: UUID,
        client_id: UUID,
        service_id: UUID,
        desired_datetime: datetime,
        status: str = ServiceRequestStatus.REQUESTED.value,
        address: Optional[str] = None,
        created_at: Optional[datetime] = None,
        accepted_provider_id: Optional[UUID] = None,
        departure_address: Optional[str] = None,
        service_price: Optional[Decimal] = None,
        travel_price: Optional[Decimal] = None,
        total_price: Optional[Decimal] = None,
        accepted_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        # Campos de deslocamento (Fase 1)
        travel_started_at: Optional[datetime] = None,
        route_calculated_at: Optional[datetime] = None,
        estimated_arrival_at: Optional[datetime] = None,
        travel_duration_minutes: Optional[int] = None,
        travel_distance_km: Optional[Decimal] = None,
        # Campos de chegada / início do serviço (Fase 1)
        provider_arrived_at: Optional[datetime] = None,
        client_confirmed_provider_arrival_at: Optional[datetime] = None,
        service_started_at: Optional[datetime] = None,
        # Rastreabilidade da ACL Logística (Fase 1)
        logistics_reference: Optional[str] = None,
        # Campos financeiros pós-serviço (Fase 1 pagamento)
        service_finished_at: Optional[datetime] = None,
        payment_requested_at: Optional[datetime] = None,
        payment_processing_started_at: Optional[datetime] = None,
        payment_approved_at: Optional[datetime] = None,
        payment_refused_at: Optional[datetime] = None,
        service_concluded_at: Optional[datetime] = None,
        payment_amount: Optional[Decimal] = None,
        payment_last_status: Optional[str] = None,
        payment_provider: Optional[str] = None,
        payment_reference: Optional[str] = None,
        payment_attempt_count: Optional[int] = None,
    ):
        self.id = id
        self.client_id = client_id
        self.service_id = service_id
        self.desired_datetime = desired_datetime
        self.status = self._normalize_status(status)
        self.address = address
        self.created_at = created_at or datetime.utcnow()
        self.accepted_provider_id = accepted_provider_id
        self.departure_address = departure_address
        self.service_price = service_price
        self.travel_price = travel_price
        self.total_price = total_price
        self.accepted_at = accepted_at
        self.expires_at = expires_at
        self.travel_started_at = travel_started_at
        self.route_calculated_at = route_calculated_at
        self.estimated_arrival_at = estimated_arrival_at
        self.travel_duration_minutes = travel_duration_minutes
        self.travel_distance_km = travel_distance_km
        self.provider_arrived_at = provider_arrived_at
        self.client_confirmed_provider_arrival_at = client_confirmed_provider_arrival_at
        self.service_started_at = service_started_at
        self.logistics_reference = logistics_reference
        # Campos financeiros pós-serviço
        self.service_finished_at = service_finished_at
        self.payment_requested_at = payment_requested_at
        self.payment_processing_started_at = payment_processing_started_at
        self.payment_approved_at = payment_approved_at
        self.payment_refused_at = payment_refused_at
        self.service_concluded_at = service_concluded_at
        self.payment_amount = payment_amount
        self.payment_last_status = payment_last_status
        self.payment_provider = payment_provider
        self.payment_reference = payment_reference
        self.payment_attempt_count = payment_attempt_count

        self.validate()

    def _normalize_status(
        self, status: Optional[Union[str, ServiceRequestStatus]]
    ) -> str:
        if isinstance(status, ServiceRequestStatus):
            return status.value

        if isinstance(status, str):
            normalized_status = status.strip().upper()
            valid_statuses = {item.value for item in ServiceRequestStatus}

            if normalized_status in valid_statuses:
                return normalized_status

        raise ValueError("Invalid service request status.")

    def _current_reference_datetime(self) -> datetime:
        if self.desired_datetime.tzinfo is not None:
            return datetime.now(tz=self.desired_datetime.tzinfo)
        return datetime.utcnow()

    def validate(self) -> bool:
        if not isinstance(self.id, UUID):
            raise ValueError("ID must be a UUID.")

        if not isinstance(self.client_id, UUID):
            raise ValueError("Client ID must be a UUID.")

        if not isinstance(self.service_id, UUID):
            raise ValueError("Service ID must be a UUID.")

        if not isinstance(self.desired_datetime, datetime):
            raise ValueError("Desired datetime must be a datetime.")

        valid_statuses = {item.value for item in ServiceRequestStatus}
        if self.status not in valid_statuses:
            raise ValueError("Invalid service request status.")

        if self.address is not None and not isinstance(self.address, str):
            raise ValueError("Address must be a string or None.")

        if not isinstance(self.created_at, datetime):
            raise ValueError("Created at must be a datetime.")

        if self.accepted_provider_id is not None and not isinstance(
            self.accepted_provider_id, UUID
        ):
            raise ValueError("Accepted provider ID must be a UUID or None.")

        if self.departure_address is not None and not isinstance(
            self.departure_address, str
        ):
            raise ValueError("Departure address must be a string or None.")

        if self.service_price is not None and not isinstance(
            self.service_price, Decimal
        ):
            raise ValueError("Service price must be a Decimal or None.")

        if self.travel_price is not None and not isinstance(self.travel_price, Decimal):
            raise ValueError("Travel price must be a Decimal or None.")

        if self.total_price is not None and not isinstance(self.total_price, Decimal):
            raise ValueError("Total price must be a Decimal or None.")

        if self.accepted_at is not None and not isinstance(self.accepted_at, datetime):
            raise ValueError("Accepted at must be a datetime or None.")

        if self.expires_at is not None and not isinstance(self.expires_at, datetime):
            raise ValueError("Expires at must be a datetime or None.")

        if self.travel_started_at is not None and not isinstance(
            self.travel_started_at, datetime
        ):
            raise ValueError("travel_started_at must be a datetime or None.")

        if self.route_calculated_at is not None and not isinstance(
            self.route_calculated_at, datetime
        ):
            raise ValueError("route_calculated_at must be a datetime or None.")

        if self.estimated_arrival_at is not None and not isinstance(
            self.estimated_arrival_at, datetime
        ):
            raise ValueError("estimated_arrival_at must be a datetime or None.")

        if self.travel_duration_minutes is not None and not isinstance(
            self.travel_duration_minutes, int
        ):
            raise ValueError("travel_duration_minutes must be an int or None.")

        if self.travel_distance_km is not None and not isinstance(
            self.travel_distance_km, Decimal
        ):
            raise ValueError("travel_distance_km must be a Decimal or None.")

        if self.provider_arrived_at is not None and not isinstance(
            self.provider_arrived_at, datetime
        ):
            raise ValueError("provider_arrived_at must be a datetime or None.")

        if self.client_confirmed_provider_arrival_at is not None and not isinstance(
            self.client_confirmed_provider_arrival_at, datetime
        ):
            raise ValueError(
                "client_confirmed_provider_arrival_at must be a datetime or None."
            )

        if self.service_started_at is not None and not isinstance(
            self.service_started_at, datetime
        ):
            raise ValueError("service_started_at must be a datetime or None.")

        if self.logistics_reference is not None and not isinstance(
            self.logistics_reference, str
        ):
            raise ValueError("logistics_reference must be a string or None.")

        if self.service_finished_at is not None and not isinstance(
            self.service_finished_at, datetime
        ):
            raise ValueError("service_finished_at must be a datetime or None.")

        if self.payment_requested_at is not None and not isinstance(
            self.payment_requested_at, datetime
        ):
            raise ValueError("payment_requested_at must be a datetime or None.")

        if self.payment_processing_started_at is not None and not isinstance(
            self.payment_processing_started_at, datetime
        ):
            raise ValueError(
                "payment_processing_started_at must be a datetime or None."
            )

        if self.payment_approved_at is not None and not isinstance(
            self.payment_approved_at, datetime
        ):
            raise ValueError("payment_approved_at must be a datetime or None.")

        if self.payment_refused_at is not None and not isinstance(
            self.payment_refused_at, datetime
        ):
            raise ValueError("payment_refused_at must be a datetime or None.")

        if self.service_concluded_at is not None and not isinstance(
            self.service_concluded_at, datetime
        ):
            raise ValueError("service_concluded_at must be a datetime or None.")

        if self.payment_amount is not None and not isinstance(
            self.payment_amount, Decimal
        ):
            raise ValueError("payment_amount must be a Decimal or None.")

        if self.payment_amount is not None and self.payment_amount <= Decimal("0"):
            raise ValueError("payment_amount must be greater than zero.")

        if self.payment_last_status is not None and not isinstance(
            self.payment_last_status, str):
            raise ValueError("payment_last_status must be a string or None.")

        if self.payment_last_status is not None:
            valid_snapshot_values = {item.value for item in PaymentStatusSnapshot}
            if self.payment_last_status not in valid_snapshot_values:
                raise ValueError(
                    f"payment_last_status must be one of {sorted(valid_snapshot_values)} or None."
                )


        if self.payment_provider is not None and not isinstance(
            self.payment_provider, str
        ):
            raise ValueError("payment_provider must be a string or None.")

        if self.payment_reference is not None and not isinstance(
            self.payment_reference, str
        ):
            raise ValueError("payment_reference must be a string or None.")

        if self.payment_attempt_count is not None and not isinstance(
            self.payment_attempt_count, int
        ):
            raise ValueError("payment_attempt_count must be an int or None.")
        
        if self.payment_attempt_count is not None and self.payment_attempt_count < 0:
            raise ValueError("payment_attempt_count must be zero or a positive integer.")

        self._validate_non_confirmed_cancelled_state()
        self._validate_no_travel_fields_in_pre_operational_state()
        self._validate_confirmed_state()
        self._validate_in_transit_state()
        self._validate_arrived_state()
        self._validate_in_progress_state()
        self._validate_awaiting_payment_state()
        self._validate_payment_processing_state()
        self._validate_completed_state()
        self._validate_total_price_consistency()
        self._validate_operational_temporal_order()
        self._validate_financial_temporal_order()

        return True

    def _validate_confirmed_state(self) -> bool:
        if self.status != ServiceRequestStatus.CONFIRMED.value:
            return True

        if self.accepted_provider_id is None:
            raise ValueError(
                "Confirmed service request must have accepted_provider_id."
            )

        if not self.departure_address:
            raise ValueError("Confirmed service request must have departure_address.")

        if self.service_price is None:
            raise ValueError("Confirmed service request must have service_price.")

        if self.travel_price is None:
            raise ValueError("Confirmed service request must have travel_price.")

        if self.total_price is None:
            raise ValueError("Confirmed service request must have total_price.")

        if self.accepted_at is None:
            raise ValueError("Confirmed service request must have accepted_at.")

        return True

    def _validate_in_transit_state(self) -> bool:
        if self.status != ServiceRequestStatus.IN_TRANSIT.value:
            return True

        if self.accepted_provider_id is None:
            raise ValueError(
                "IN_TRANSIT service request must have accepted_provider_id."
            )

        if not self.departure_address:
            raise ValueError("IN_TRANSIT service request must have departure_address.")

        if self.service_price is None:
            raise ValueError("IN_TRANSIT service request must have service_price.")

        if self.travel_price is None:
            raise ValueError("IN_TRANSIT service request must have travel_price.")

        if self.total_price is None:
            raise ValueError("IN_TRANSIT service request must have total_price.")

        if self.accepted_at is None:
            raise ValueError("IN_TRANSIT service request must have accepted_at.")

        if self.travel_started_at is None:
            raise ValueError("IN_TRANSIT service request must have travel_started_at.")

        if self.route_calculated_at is None:
            raise ValueError(
                "IN_TRANSIT service request must have route_calculated_at."
            )

        if self.estimated_arrival_at is None:
            raise ValueError(
                "IN_TRANSIT service request must have estimated_arrival_at."
            )

        if self.travel_duration_minutes is None:
            raise ValueError(
                "IN_TRANSIT service request must have travel_duration_minutes."
            )

        # IN_TRANSIT não deve ter campos de chegada ou início de serviço
        if self.provider_arrived_at is not None:
            raise ValueError(
                "IN_TRANSIT service request must not have provider_arrived_at."
            )

        if self.service_started_at is not None:
            raise ValueError(
                "IN_TRANSIT service request must not have service_started_at."
            )

        return True

    def _validate_arrived_state(self) -> bool:
        if self.status != ServiceRequestStatus.ARRIVED.value:
            return True

        if self.accepted_provider_id is None:
            raise ValueError("ARRIVED service request must have accepted_provider_id.")

        if not self.departure_address:
            raise ValueError("ARRIVED service request must have departure_address.")

        if self.service_price is None:
            raise ValueError("ARRIVED service request must have service_price.")

        if self.travel_price is None:
            raise ValueError("ARRIVED service request must have travel_price.")

        if self.total_price is None:
            raise ValueError("ARRIVED service request must have total_price.")

        if self.accepted_at is None:
            raise ValueError("ARRIVED service request must have accepted_at.")

        if self.travel_started_at is None:
            raise ValueError("ARRIVED service request must have travel_started_at.")

        if self.route_calculated_at is None:
            raise ValueError("ARRIVED service request must have route_calculated_at.")

        if self.estimated_arrival_at is None:
            raise ValueError("ARRIVED service request must have estimated_arrival_at.")

        if self.travel_duration_minutes is None:
            raise ValueError(
                "ARRIVED service request must have travel_duration_minutes."
            )

        if self.provider_arrived_at is None:
            raise ValueError("ARRIVED service request must have provider_arrived_at.")

        # ARRIVED não deve ter campos de início de serviço
        if self.service_started_at is not None:
            raise ValueError(
                "ARRIVED service request must not have service_started_at."
            )

        if self.client_confirmed_provider_arrival_at is not None:
            raise ValueError(
                "ARRIVED service request must not have client_confirmed_provider_arrival_at."
            )

        return True

    def _validate_in_progress_state(self) -> bool:
        if self.status != ServiceRequestStatus.IN_PROGRESS.value:
            return True

        if self.accepted_provider_id is None:
            raise ValueError(
                "IN_PROGRESS service request must have accepted_provider_id."
            )

        if not self.departure_address:
            raise ValueError("IN_PROGRESS service request must have departure_address.")

        if self.service_price is None:
            raise ValueError("IN_PROGRESS service request must have service_price.")

        if self.travel_price is None:
            raise ValueError("IN_PROGRESS service request must have travel_price.")

        if self.total_price is None:
            raise ValueError("IN_PROGRESS service request must have total_price.")

        if self.accepted_at is None:
            raise ValueError("IN_PROGRESS service request must have accepted_at.")

        if self.travel_started_at is None:
            raise ValueError("IN_PROGRESS service request must have travel_started_at.")

        if self.route_calculated_at is None:
            raise ValueError(
                "IN_PROGRESS service request must have route_calculated_at."
            )

        if self.estimated_arrival_at is None:
            raise ValueError(
                "IN_PROGRESS service request must have estimated_arrival_at."
            )

        if self.travel_duration_minutes is None:
            raise ValueError(
                "IN_PROGRESS service request must have travel_duration_minutes."
            )

        if self.provider_arrived_at is None:
            raise ValueError(
                "IN_PROGRESS service request must have provider_arrived_at."
            )

        if self.client_confirmed_provider_arrival_at is None:
            raise ValueError(
                "IN_PROGRESS service request must have client_confirmed_provider_arrival_at."
            )

        if self.service_started_at is None:
            raise ValueError(
                "IN_PROGRESS service request must have service_started_at."
            )

        # IN_PROGRESS: campos financeiros pós-serviço devem ser nulos
        financial_fields = [
            self.service_finished_at,
            self.payment_requested_at,
            self.payment_processing_started_at,
            self.payment_approved_at,
            self.payment_refused_at,
            self.service_concluded_at,
            self.payment_amount,
            self.payment_last_status,
            self.payment_provider,
            self.payment_reference,
            self.payment_attempt_count,
        ]
        if any(f is not None for f in financial_fields):
            raise ValueError(
                "IN_PROGRESS service request must not have financial post-service fields set."
            )

        return True

    def _validate_total_price_consistency(self) -> bool:
        prices = [self.service_price, self.travel_price, self.total_price]

        if all(price is None for price in prices):
            return True

        if (
            self.service_price is None
            or self.travel_price is None
            or self.total_price is None
        ):
            raise ValueError(
                "Service price, travel price and total price must be informed together."
            )

        expected_total = self.service_price + self.travel_price
        if self.total_price != expected_total:
            raise ValueError(
                f"Total price must be equal to service_price + travel_price. "
                f"Expected {expected_total}, got {self.total_price}."
            )
        return True

    def _validate_non_confirmed_cancelled_state(self) -> bool:
        # Status que permitem campos de aceitação/precificação
        statuses_with_acceptance = (
            _OPERATIONAL_STATUSES
            | _FINANCIAL_STATUSES
            | {ServiceRequestStatus.CANCELLED.value}
        )
        if self.status in statuses_with_acceptance:
            return True

        acceptance_fields = [
            self.accepted_provider_id,
            self.departure_address,
            self.service_price,
            self.travel_price,
            self.total_price,
            self.accepted_at,
        ]

        if any(field is not None for field in acceptance_fields):
            raise ValueError(
                "Only confirmed or cancelled service requests can have acceptance and pricing fields filled."
            )
        return True

    def _validate_no_travel_fields_in_pre_operational_state(self) -> bool:
        """Rejeita campos do ciclo operacional (deslocamento/chegada) em status pré-operacionais."""
        all_post_confirmation = _OPERATIONAL_STATUSES | _FINANCIAL_STATUSES
        if (
            self.status in all_post_confirmation
            and self.status != ServiceRequestStatus.CONFIRMED.value
        ):
            return True

        travel_fields = [
            self.travel_started_at,
            self.route_calculated_at,
            self.estimated_arrival_at,
            self.travel_duration_minutes,
            self.travel_distance_km,
            self.provider_arrived_at,
            self.client_confirmed_provider_arrival_at,
            self.service_started_at,
        ]

        if any(field is not None for field in travel_fields):
            raise ValueError(
                "Travel and arrival fields can only be set on operational service requests (IN_TRANSIT,IN_PROGRESS OR  ARRIVED)."
            )
        return True

    def _validate_operational_temporal_order(self) -> bool:
        """Valida a coerência temporal entre os campos do ciclo operacional."""
        pairs = [
            (
                self.accepted_at,
                self.travel_started_at,
                "accepted_at",
                "travel_started_at",
            ),
            (
                self.travel_started_at,
                self.estimated_arrival_at,
                "travel_started_at",
                "estimated_arrival_at",
            ),
            (
                self.travel_started_at,
                self.provider_arrived_at,
                "travel_started_at",
                "provider_arrived_at",
            ),
            (
                self.provider_arrived_at,
                self.client_confirmed_provider_arrival_at,
                "provider_arrived_at",
                "client_confirmed_provider_arrival_at",
            ),
            (
                self.client_confirmed_provider_arrival_at,
                self.service_started_at,
                "client_confirmed_provider_arrival_at",
                "service_started_at",
            ),
        ]
        for earlier, later, earlier_name, later_name in pairs:
            if earlier is not None and later is not None and earlier > later:
                raise ValueError(f"{earlier_name} must not be after {later_name}.")
        return True

    def _validate_awaiting_payment_state(self) -> bool:
        if self.status != ServiceRequestStatus.AWAITING_PAYMENT.value:
            return True

        if self.service_started_at is None:
            raise ValueError(
                "AWAITING_PAYMENT service request must have service_started_at."
            )

        if self.service_finished_at is None:
            raise ValueError(
                "AWAITING_PAYMENT service request must have service_finished_at."
            )

        if self.payment_requested_at is None:
            raise ValueError(
                "AWAITING_PAYMENT service request must have payment_requested_at."
            )

        if self.service_concluded_at is not None:
            raise ValueError(
                "AWAITING_PAYMENT service request must not have service_concluded_at."
            )

        if self.payment_approved_at is not None:
            raise ValueError(
                "AWAITING_PAYMENT service request must not have payment_approved_at."
            )

        return True

    def _validate_payment_processing_state(self) -> bool:
        if self.status != ServiceRequestStatus.PAYMENT_PROCESSING.value:
            return True

        if self.service_started_at is None:
            raise ValueError(
                "PAYMENT_PROCESSING service request must have service_started_at."
            )

        if self.service_finished_at is None:
            raise ValueError(
                "PAYMENT_PROCESSING service request must have service_finished_at."
            )

        if self.payment_requested_at is None:
            raise ValueError(
                "PAYMENT_PROCESSING service request must have payment_requested_at."
            )

        if self.payment_processing_started_at is None:
            raise ValueError(
                "PAYMENT_PROCESSING service request must have payment_processing_started_at."
            )

        if self.service_concluded_at is not None:
            raise ValueError(
                "PAYMENT_PROCESSING service request must not have service_concluded_at."
            )

        if self.payment_approved_at is not None:
            raise ValueError(
                "PAYMENT_PROCESSING service request must not have payment_approved_at."
            )

        return True

    def _validate_completed_state(self) -> bool:
        if self.status != ServiceRequestStatus.COMPLETED.value:
            return True

        if self.service_finished_at is None:
            raise ValueError("COMPLETED service request must have service_finished_at.")

        if self.payment_approved_at is None:
            raise ValueError("COMPLETED service request must have payment_approved_at.")

        if self.service_concluded_at is None:
            raise ValueError(
                "COMPLETED service request must have service_concluded_at."
            )

        if self.payment_refused_at is not None:
            raise ValueError(
                "COMPLETED service request must not have payment_refused_at."
            )

        if self.payment_last_status != PaymentStatusSnapshot.APPROVED.value:
            raise ValueError(
                "COMPLETED service request must have payment_last_status = APPROVED."
            )

        return True

    def _validate_financial_temporal_order(self) -> bool:
        """Valida a coerência temporal dos campos financeiros."""
        pairs = [
            (
                self.service_started_at,
                self.service_finished_at,
                "service_started_at",
                "service_finished_at",
            ),
            (
                self.service_finished_at,
                self.payment_requested_at,
                "service_finished_at",
                "payment_requested_at",
            ),
            (
                self.payment_requested_at,
                self.payment_processing_started_at,
                "payment_requested_at",
                "payment_processing_started_at",
            ),
            (
                self.payment_processing_started_at,
                self.payment_approved_at,
                "payment_processing_started_at",
                "payment_approved_at",
            ),
            (
                self.payment_approved_at,
                self.service_concluded_at,
                "payment_approved_at",
                "service_concluded_at",
            ),
            (
                self.payment_processing_started_at,
                self.payment_refused_at,
                "payment_processing_started_at",
                "payment_refused_at",
            ),
        ]
        for earlier, later, earlier_name, later_name in pairs:
            if earlier is not None and later is not None and earlier > later:
                raise ValueError(f"{earlier_name} must not be after {later_name}.")
        return True
