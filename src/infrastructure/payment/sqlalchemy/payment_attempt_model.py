import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from infrastructure.api.database import Base


class PaymentAttemptModel(Base):
    __tablename__ = "tb_payment_attempts"
    __table_args__ = (
        UniqueConstraint("service_request_id", "attempt_number", name="uq_payment_attempt_number"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    service_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tb_service_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attempt_number = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, nullable=False, default="REQUESTED", index=True)

    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    refused_at = Column(DateTime, nullable=True)

    provider = Column(String, nullable=True)
    external_reference = Column(String, nullable=True, index=True)
    refusal_reason = Column(String, nullable=True)
    provider_message = Column(String, nullable=True)

    service_request = relationship(
        "ServiceRequestModel",
        foreign_keys=[service_request_id],
    )