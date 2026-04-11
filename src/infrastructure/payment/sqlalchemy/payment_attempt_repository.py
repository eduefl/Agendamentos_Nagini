from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.orm import Session
from domain.payment.payment_attempt_entity import PaymentAttempt
from domain.payment.payment_attempt_repository_interface import PaymentAttemptRepositoryInterface
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from infrastructure.payment.sqlalchemy.payment_attempt_model import PaymentAttemptModel
class PaymentAttemptRepository(PaymentAttemptRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session
    def _model_to_entity(self, model: PaymentAttemptModel) -> PaymentAttempt:
        return PaymentAttempt(
            id=model.id,
            service_request_id=model.service_request_id,
            attempt_number=model.attempt_number,
            amount=model.amount,
            status=model.status,
            requested_at=model.requested_at,
            processing_started_at=model.processing_started_at,
            processed_at=model.processed_at,
            approved_at=model.approved_at,
            refused_at=model.refused_at,
            provider=model.provider,
            external_reference=model.external_reference,
            refusal_reason=model.refusal_reason,
            provider_message=model.provider_message,
        )
    def _entity_to_model(self, entity: PaymentAttempt) -> PaymentAttemptModel:
        return PaymentAttemptModel(
            id=entity.id,
            service_request_id=entity.service_request_id,
            attempt_number=entity.attempt_number,
            amount=entity.amount,
            status=entity.status,
            requested_at=entity.requested_at,
            processing_started_at=entity.processing_started_at,
            processed_at=entity.processed_at,
            approved_at=entity.approved_at,
            refused_at=entity.refused_at,
            provider=entity.provider,
            external_reference=entity.external_reference,
            refusal_reason=entity.refusal_reason,
            provider_message=entity.provider_message,
        )
    def create(self, attempt: PaymentAttempt) -> PaymentAttempt:
        model = self._entity_to_model(attempt)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._model_to_entity(model)
    def find_latest_by_service_request_id(
        self,
        service_request_id: UUID,
    ) -> Optional[PaymentAttempt]:
        model = (
            self.session.query(PaymentAttemptModel)
            .filter(PaymentAttemptModel.service_request_id == service_request_id)
            .order_by(PaymentAttemptModel.attempt_number.desc())
            .first()
        )
        if model is None:
            return None
        return self._model_to_entity(model)
    def find_by_external_reference(
        self,
        external_reference: str,
    ) -> Optional[PaymentAttempt]:
        model = (
            self.session.query(PaymentAttemptModel)
            .filter(PaymentAttemptModel.external_reference == external_reference)
            .first()
        )
        if model is None:
            return None
        return self._model_to_entity(model)
    def mark_processing(
        self,
        attempt_id: UUID,
    ) -> Optional[PaymentAttempt]:
        now = datetime.utcnow()
        result = self.session.execute(
            update(PaymentAttemptModel)
            .where(
                PaymentAttemptModel.id == attempt_id,
                PaymentAttemptModel.status == PaymentAttemptStatus.REQUESTED.value,
            )
            .values(
                status=PaymentAttemptStatus.PROCESSING.value,
                processing_started_at=now,
            )
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount == 0:
            return None
        self.session.commit()
        model = (
            self.session.query(PaymentAttemptModel)
            .filter(PaymentAttemptModel.id == attempt_id)
            .first()
        )
        return self._model_to_entity(model)
    def mark_approved(
        self,
        attempt_id: UUID,
    ) -> Optional[PaymentAttempt]:
        now = datetime.utcnow()
        result = self.session.execute(
            update(PaymentAttemptModel)
            .where(
                PaymentAttemptModel.id == attempt_id,
                PaymentAttemptModel.status == PaymentAttemptStatus.PROCESSING.value,
            )
            .values(
                status=PaymentAttemptStatus.APPROVED.value,
                approved_at=now,
                processed_at=now,
            )
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount == 0:
            return None
        self.session.commit()
        model = (
            self.session.query(PaymentAttemptModel)
            .filter(PaymentAttemptModel.id == attempt_id)
            .first()
        )
        return self._model_to_entity(model)
    def mark_refused(
        self,
        attempt_id: UUID,
        refusal_reason: Optional[str] = None,
    ) -> Optional[PaymentAttempt]:
        now = datetime.utcnow()
        values = {
            "status": PaymentAttemptStatus.REFUSED.value,
            "refused_at": now,
            "processed_at": now,
        }
        if refusal_reason is not None:
            values["refusal_reason"] = refusal_reason
        result = self.session.execute(
            update(PaymentAttemptModel)
            .where(
                PaymentAttemptModel.id == attempt_id,
                PaymentAttemptModel.status == PaymentAttemptStatus.PROCESSING.value,
            )
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount == 0:
            return None
        self.session.commit()
        model = (
            self.session.query(PaymentAttemptModel)
            .filter(PaymentAttemptModel.id == attempt_id)
            .first()
        )
        return self._model_to_entity(model)
    def count_by_service_request_id(
        self,
        service_request_id: UUID,
    ) -> int:
        return (
            self.session.query(PaymentAttemptModel)
            .filter(PaymentAttemptModel.service_request_id == service_request_id)
            .count()
        )

    def record_gateway_reference(
        self,
        attempt_id: UUID,
        provider: str,
        external_reference: str,
        provider_message: Optional[str] = None,
    ) -> Optional[PaymentAttempt]:
        values = {
            "provider": provider,
            "external_reference": external_reference,
        }
        if provider_message is not None:
            values["provider_message"] = provider_message
        result = self.session.execute(
            update(PaymentAttemptModel)
            .where(PaymentAttemptModel.id == attempt_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        if result.rowcount == 0:
            return None
        self.session.commit()
        model = (
            self.session.query(PaymentAttemptModel)
            .filter(PaymentAttemptModel.id == attempt_id)
            .first()
        )
        return self._model_to_entity(model)