from datetime import datetime
import uuid

from infrastructure.api.database import Base
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ServiceModel(Base):
    __tablename__ = "tb_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    provider_services = relationship(
        "ProviderServiceModel",
        back_populates="service",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


