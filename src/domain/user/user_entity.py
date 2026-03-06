from uuid import UUID

class User:
	
	id: UUID
	name: str

	def __init__(self, id: UUID, name: str):
		self.id = id
		self.name = name
		self.validate()

	def validate(self):
		if not isinstance(self.id, UUID):
			raise ValueError("ID must be a valid UUID.")
		if not isinstance(self.name, str):
			raise ValueError("Name must be a string.")
		if not self.name:
			raise ValueError("Name cannot be empty.")
		

	def __str__(self):
		return f"User(id={self.id}, name='{self.name}')"
