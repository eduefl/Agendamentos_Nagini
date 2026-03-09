import xml.etree.ElementTree as ET
from functools import singledispatchmethod

from usecases.task.list_tasks_from_user.list_tasks_from_user_dto import ListTasksFromUserOutputDTO
from usecases.task.delete_task.delete_task_dto import DeleteTaskOutputDTO
from usecases.task.update_task.update_task_dto import UpdateTaskOutputDTO
from usecases.task.get_task_by_id.get_task_by_id_dto import getTaskByIdOutputDTO
from usecases.task.create_task.create_task_dto import createTaskOutputDTO

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
	def _(task_dto: UpdateTaskOutputDTO) -> dict:
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
	
	
	@toJSON.register
	@staticmethod
	def _(task_dto: DeleteTaskOutputDTO) -> dict:
		return {
			"message": str(task_dto.message),
		}
	
	@toJSON.register
	@staticmethod
	def _(task_dto: ListTasksFromUserOutputDTO) -> dict:
	
		return {"tasks": 
		  			[{"id": str(task.id),
					"title": task.title,
					"description": task.description,
					"user_id": str(task.user_id),
					"completed": task.completed} 
				for task in task_dto.tasks]
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


	@toXml.register
	@staticmethod
	def _(task_dto: UpdateTaskOutputDTO) -> str:
		task_data = ET.Element("task")
		ET.SubElement(task_data, "id").text = str(task_dto.id)
		ET.SubElement(task_data, "title").text = task_dto.title
		ET.SubElement(task_data, "description").text = task_dto.description
		ET.SubElement(task_data, "user_id").text = str(task_dto.user_id)
		ET.SubElement(task_data, "completed").text = str(task_dto.completed)
		return ET.tostring(task_data, encoding='unicode')
	

	@toXml.register
	@staticmethod
	def _(task_dto: DeleteTaskOutputDTO) -> str:
		task_data = ET.Element("task")
		ET.SubElement(task_data, "message").text = str(task_dto.message)
		return ET.tostring(task_data, encoding='unicode')
	
		

	@toXml.register
	@staticmethod
	def _(task_dto: ListTasksFromUserOutputDTO) -> str:
		tasks_data = ET.Element("tasks")
		for task in task_dto.tasks:
			task_element = ET.SubElement(tasks_data, "task")
			ET.SubElement(task_element, "id").text = str(task.id)
			ET.SubElement(task_element, "title").text = task.title
			ET.SubElement(task_element, "description").text = task.description
			ET.SubElement(task_element, "user_id").text = str(task.user_id)
			ET.SubElement(task_element, "completed").text = str(task.completed)
		return ET.tostring(tasks_data, encoding='unicode')
	
		
