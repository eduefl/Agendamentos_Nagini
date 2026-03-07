from sqlalchemy import Column, String, ForeignKey, Boolean
from infrastructure.api.database import Base
from sqlalchemy.dialects.postgresql import UUID

class TaskModel(Base):

	__tablename__ = "tb_tasks"

	id = Column(UUID, primary_key=True, index=True)
	user_id = Column(UUID, ForeignKey("tb_users.id", ondelete="CASCADE"))
	title = Column(String)
	description = Column(String)
	completed = Column(Boolean, default=False)
	


