from datetime import datetime
import uuid

from infrastructure.api.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class ProviderServiceModel(Base):
    __tablename__ = "tb_provider_services"

    __table_args__ = (
        UniqueConstraint("provider_id", "service_id", name="uq_provider_service"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    provider_id = Column(
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
    price = Column(Numeric(10, 2), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    provider = relationship("UserModel", back_populates="provider_services")
    service = relationship("ServiceModel", back_populates="provider_services")
