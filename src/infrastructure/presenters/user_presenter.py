
import xml.etree.ElementTree as ET
from usecases.user.update_user.update_user_dto import UpdateUserOutputDTO
from usecases.user.add_user.add_user_dto import AddUserOutputDTO
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdOutputDTO
from usecases.user.list_users.list_users_dto import ListUsersOutputDTO
from functools import singledispatchmethod

class UserPresenter :
	@singledispatchmethod #decorador singledispatchmethod da biblioteca padrão, usado para criar métodos que mudam conforme o tipo do argumento. 
	@staticmethod
	def toJSON(user_dto) -> dict:
		raise NotImplementedError("Unsupported type")
	
	@toJSON.register #decorador para registrar uma implementação específica do método toJSON para um tipo específico de argumento.	
	@staticmethod #decorador para indicar que o método é estático, ou seja, pode ser chamado sem a necessidade de criar uma instância da classe. Ele é usado aqui para indicar que o método toJSON pode ser chamado diretamente na classe UserPresenter, sem a necessidade de criar um objeto dessa classe. Isso é útil porque o método toJSON não depende de nenhum estado interno da classe e pode ser usado como uma função utilitária para converter os DTOs em JSON.	
	def _(user_dto: findUserByIdOutputDTO) -> dict: #O nome do método é irrelevante, o importante é o tipo do argumento. O método é registrado para ser chamado quando o argumento for do tipo findUserByIdOutputDTO.
		return {
			"id": str(user_dto.id),
			"name": user_dto.name
		}
	
	@toJSON.register #decorador para registrar uma implementação específica do método toJSON para um tipo específico de argumento.
	@staticmethod
	def _(user_dto: AddUserOutputDTO) -> dict:
		return {
			"name": user_dto.name,
			"id": str(user_dto.id)
		}


	@toJSON.register #decorador para registrar uma implementação específica do método toJSON para um tipo específico de argumento.
	@staticmethod
	def _(user_dto: UpdateUserOutputDTO) -> dict: #O nome do método é irrelevante, o importante é o tipo do argumento. O método é registrado para ser chamado quando o argumento for do tipo UpdateUserOutputDTO.	
		return {
			"name": user_dto.name,
			"id": str(user_dto.id)
		}

	@toJSON.register
	@staticmethod
	def _(user_dto: ListUsersOutputDTO) -> dict:
		jRet = []
		#Funcional
		# jRet = list(map(lambda user: {"name": user.name, "id": str(user.id)}, user_dto.users))

		#list comprehension 
		jRet = [{"name": user.name, "id": str(user.id)} for user in user_dto.users]


		#Traditional (Programação imperativa)
		# for user in user_dto.users:
		# 	jRet.append( {"name": user.name,"id": str(user.id)}) 
		return jRet

	@singledispatchmethod
	@staticmethod
	def toXml(user_dto) -> str:
		raise NotImplementedError("Unsupported type")

	@toXml.register
	@staticmethod
	def _(user_dto: findUserByIdOutputDTO) -> str:
		user_data = ET.Element("user")
		ET.SubElement(user_data, "id").text = str(user_dto.id)
		ET.SubElement(user_data, "name").text = user_dto.name
		return ET.tostring(user_data, encoding='unicode')

	@toXml.register
	@staticmethod
	def _(user_dto: AddUserOutputDTO) -> str:
		user_data = ET.Element("user")
		ET.SubElement(user_data, "name").text = user_dto.name
		ET.SubElement(user_data, "id").text = str(user_dto.id)
		return ET.tostring(user_data, encoding='unicode')
	
	@toXml.register
	@staticmethod
	def _(user_dto: UpdateUserOutputDTO) -> str:
		user_data = ET.Element("user")
		ET.SubElement(user_data, "name").text = user_dto.name
		ET.SubElement(user_data, "id").text = str(user_dto.id)
		return ET.tostring(user_data, encoding='unicode')
	
	@toXml.register
	@staticmethod
	def _(user_dto: ListUsersOutputDTO) -> str:
		user_data = ET.Element("data")
		for user in user_dto.users:
			user_element = ET.SubElement(user_data, "user")
			ET.SubElement(user_element, "name").text = user.name
			ET.SubElement(user_element, "id").text = str(user.id)
		return ET.tostring(user_data, encoding='unicode')
	
		