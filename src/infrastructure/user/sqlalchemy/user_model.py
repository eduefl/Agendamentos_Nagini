import uuid

from infrastructure.api.database import Base
from sqlalchemy import Column, String, Boolean, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

user_roles = Table(
    "tb_user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("tb_roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

class RoleModel(Base):
    __tablename__ = "tb_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)

    users = relationship("UserModel", secondary=user_roles, back_populates="roles")


class UserModel(Base):
    __tablename__ = "tb_users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    roles = relationship("RoleModel", secondary=user_roles, back_populates="users", lazy="selectin")

    