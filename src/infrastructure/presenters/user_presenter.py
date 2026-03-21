import xml.etree.ElementTree as ET
from functools import singledispatchmethod

from usecases.user.add_user.add_user_dto import AddUserOutputDTO
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdOutputDTO
from usecases.user.list_users.list_users_dto import ListUsersOutputDTO
from usecases.user.update_user.update_user_dto import UpdateUserOutputDTO


class UserPresenter:
    @singledispatchmethod
    @staticmethod
    def toJSON(user_dto) -> dict:
        raise NotImplementedError("Unsupported type")

    @toJSON.register
    @staticmethod
    def _(user_dto: findUserByIdOutputDTO) -> dict:
        return {
            "id": str(user_dto.id),
            "name": user_dto.name,
            "email": getattr(user_dto, "email", None),
            "is_active": getattr(user_dto, "is_active", None),
            "tasks": user_dto.tasks,
            "pending_tasks": user_dto.pending_tasks,
        }

    @toJSON.register
    @staticmethod
    def _(user_dto: AddUserOutputDTO) -> dict:
        return {
            "id": str(user_dto.id),
            "name": user_dto.name,
            "email": getattr(user_dto, "email", None),
            "is_active": getattr(user_dto, "is_active", None),
        }

    @toJSON.register
    @staticmethod
    def _(user_dto: UpdateUserOutputDTO) -> dict:
        return {
            "id": str(user_dto.id),
            "name": user_dto.name,
            "email": getattr(user_dto, "email", None),
            "is_active": getattr(user_dto, "is_active", None),
        }

    @toJSON.register
    @staticmethod
    def _(user_dto: ListUsersOutputDTO) -> dict:
        # Importante: não incluir hashed_password
        return [
            {
                "id": str(user.id),
                "name": user.name,
                "email": getattr(user, "email", None),
                "is_active": getattr(user, "is_active", None),
            }
            for user in user_dto.users
        ]

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

        email = getattr(user_dto, "email", None)
        if email is not None:
            ET.SubElement(user_data, "email").text = email

        is_active = getattr(user_dto, "is_active", None)
        if is_active is not None:
            ET.SubElement(user_data, "is_active").text = str(is_active)

        for task in user_dto.tasks:
            task_element = ET.SubElement(user_data, "task")
            ET.SubElement(task_element, "id").text = str(task.id)
            ET.SubElement(task_element, "title").text = task.title
            ET.SubElement(task_element, "description").text = task.description
            ET.SubElement(task_element, "completed").text = str(task.completed)

        ET.SubElement(user_data, "pending_tasks").text = str(user_dto.pending_tasks)
        return ET.tostring(user_data, encoding="unicode")

    @toXml.register
    @staticmethod
    def _(user_dto: AddUserOutputDTO) -> str:
        user_data = ET.Element("user")
        ET.SubElement(user_data, "id").text = str(user_dto.id)
        ET.SubElement(user_data, "name").text = user_dto.name

        email = getattr(user_dto, "email", None)
        if email is not None:
            ET.SubElement(user_data, "email").text = email

        is_active = getattr(user_dto, "is_active", None)
        if is_active is not None:
            ET.SubElement(user_data, "is_active").text = str(is_active)

        return ET.tostring(user_data, encoding="unicode")

    @toXml.register
    @staticmethod
    def _(user_dto: UpdateUserOutputDTO) -> str:
        user_data = ET.Element("user")
        ET.SubElement(user_data, "id").text = str(user_dto.id)
        ET.SubElement(user_data, "name").text = user_dto.name

        email = getattr(user_dto, "email", None)
        if email is not None:
            ET.SubElement(user_data, "email").text = email

        is_active = getattr(user_dto, "is_active", None)
        if is_active is not None:
            ET.SubElement(user_data, "is_active").text = str(is_active)

        return ET.tostring(user_data, encoding="unicode")

    @toXml.register
    @staticmethod
    def _(user_dto: ListUsersOutputDTO) -> str:
        user_data = ET.Element("data")
        for user in user_dto.users:
            user_element = ET.SubElement(user_data, "user")
            ET.SubElement(user_element, "id").text = str(user.id)
            ET.SubElement(user_element, "name").text = user.name

            email = getattr(user, "email", None)
            if email is not None:
                ET.SubElement(user_element, "email").text = email

            is_active = getattr(user, "is_active", None)
            if is_active is not None:
                ET.SubElement(user_element, "is_active").text = str(is_active)

        return ET.tostring(user_data, encoding="unicode")