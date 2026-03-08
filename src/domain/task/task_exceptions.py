
from uuid import UUID
from domain.__seedwork.exceptions import NotFoundError

class TaskNotFoundError(NotFoundError):
    def __init__(self, task_id: UUID):
        super().__init__(f"Task with id {task_id} not found")
        self.task_id = task_id