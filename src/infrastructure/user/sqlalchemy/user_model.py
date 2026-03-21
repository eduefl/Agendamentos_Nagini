from infrastructure.api.database import Base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID


class UserModel(Base):

	__tablename__ = "tb_users"

	id = Column(UUID, primary_key=True, index=True, nullable=False)
	name = Column(String, index=True, nullable=False)
	email = Column(String, unique=True, index=True, nullable=False)
	hashed_password = Column(String, nullable=False)
	is_active = Column(Boolean, default=True, nullable=False)
