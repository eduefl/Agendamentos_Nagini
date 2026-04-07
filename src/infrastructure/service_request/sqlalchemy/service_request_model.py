from datetime import datetime
import uuid

from infrastructure.api.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ServiceRequestModel(Base):
    __tablename__ = "tb_service_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tb_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    desired_datetime = Column(DateTime, nullable=False, index=True)
    status = Column(String, nullable=False, default="REQUESTED", index=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    accepted_provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    departure_address = Column(String, nullable=True)
    service_price = Column(Numeric(10, 2), nullable=True)
    travel_price = Column(Numeric(10, 2), nullable=True)
    total_price = Column(Numeric(10, 2), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Fase 1 — campos de deslocamento
    travel_started_at = Column(DateTime, nullable=True)
    route_calculated_at = Column(DateTime, nullable=True)
    estimated_arrival_at = Column(DateTime, nullable=True)
    travel_duration_minutes = Column(Integer, nullable=True)
    travel_distance_km = Column(Numeric(10, 2), nullable=True)

    # Fase 1 — campos de chegada / início do serviço
    provider_arrived_at = Column(DateTime, nullable=True)
    client_confirmed_provider_arrival_at = Column(DateTime, nullable=True)
    service_started_at = Column(DateTime, nullable=True)

    # Fase 1 — rastreabilidade da ACL Logística
    logistics_reference = Column(String, nullable=True)

    client = relationship(
        "UserModel",
        foreign_keys=[client_id],
        back_populates="service_requests",
    )

    accepted_provider = relationship(
        "UserModel",
        foreign_keys=[accepted_provider_id],
        back_populates="accepted_service_requests",
    )

    service = relationship("ServiceModel", back_populates="service_requests")