

from abc import ABC, abstractmethod
from typing import Any


class TaskCaseInterface(ABC):
	@abstractmethod
	def execute(input: Any) -> Any:
		raise NotImplementedError