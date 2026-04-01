from datetime import datetime
import uuid

from infrastructure.api.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, String
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

    client = relationship("UserModel", back_populates="service_requests")
    service = relationship("ServiceModel", back_populates="service_requests")
