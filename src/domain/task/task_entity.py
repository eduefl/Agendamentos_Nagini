


from uuid import UUID


class Task:
	id : UUID
	user_id: UUID
	title: str
	description: str
	completed : bool

	def __init__(self, id: UUID, user_id: UUID, title: str, description: str, completed: bool):
		self.id = id
		self.user_id = user_id
		self.title = title
		self.description = description
		self.completed = completed
		self.validate()

	def validate(self):
		if not isinstance(self.id, UUID):
			raise ValueError("ID must be a valid UUID.")
		if not isinstance(self.user_id, UUID):
			raise ValueError("User ID must be a valid UUID.")
		if not isinstance(self.title, str):
			raise ValueError("Title must be a string.")
		if len(self.title) == 0:
			raise ValueError("Title is required")
		if not isinstance(self.description, str):
			raise ValueError("Description must be a string.")
		if len(self.description) == 0:
			raise ValueError("Description is required")
		
		if not self.title:
			raise ValueError("Title cannot be empty.")
		if not isinstance(self.completed, bool):
			raise ValueError("Completed must be a boolean.")
		return True
	
	def mark_as_completed(self) -> None:
		self.completed = True
		
	def __str__(self) -> str:
		return f"Task(id={self.id}, user_id={self.user_id}, title='{self.title}', completed={self.completed})"
	
	