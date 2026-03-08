import xml.etree.ElementTree as ET
from functools import singledispatchmethod

from usecases.task.get_task_by_id_dto import getTaskByIdOutputDTO
from usecases.task.create_task_dto import createTaskOutputDTO

class TaskPresenter :
	@singledispatchmethod
	@staticmethod
	def toJSON(task_dto) -> dict:
		raise NotImplementedError("Unsupported type")
	
	@toJSON.register
	@staticmethod
	def _(task_dto: createTaskOutputDTO) -> dict:
		return {
			"id": str(task_dto.id),
			"title": task_dto.title,
			"description": task_dto.description,
			"user_id": str(task_dto.user_id),
			"completed": task_dto.completed
		}
	
	
	@toJSON.register
	@staticmethod
	def _(task_dto: getTaskByIdOutputDTO) -> dict:
		return {
			"id": str(task_dto.id),
			"title": task_dto.title,
			"description": task_dto.description,
			"user_id": str(task_dto.user_id),
			"completed": task_dto.completed
		}
	
	


	# XML
	@singledispatchmethod
	@staticmethod
	def toXml(task_dto) -> str:
		raise NotImplementedError("Unsupported type")
	
	@toXml.register
	@staticmethod
	def _(task_dto: createTaskOutputDTO) -> str:
		task_data = ET.Element("task")
		ET.SubElement(task_data, "id").text = str(task_dto.id)
		ET.SubElement(task_data, "title").text = task_dto.title
		ET.SubElement(task_data, "description").text = task_dto.description
		ET.SubElement(task_data, "user_id").text = str(task_dto.user_id)
		ET.SubElement(task_data, "completed").text = str(task_dto.completed)
		return ET.tostring(task_data, encoding='unicode')
	

	@toXml.register
	@staticmethod
	def _(task_dto: getTaskByIdOutputDTO) -> str:
		task_data = ET.Element("task")
		ET.SubElement(task_data, "id").text = str(task_dto.id)
		ET.SubElement(task_data, "title").text = task_dto.title
		ET.SubElement(task_data, "description").text = task_dto.description
		ET.SubElement(task_data, "user_id").text = str(task_dto.user_id)
		ET.SubElement(task_data, "completed").text = str(task_dto.completed)
		return ET.tostring(task_data, encoding='unicode')