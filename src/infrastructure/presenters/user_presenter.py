import xml.etree.ElementTree as ET
from functools import singledispatchmethod
from typing import Any, Iterable, List, Optional

from usecases.user.add_user.add_user_dto import AddUserOutputDTO
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdOutputDTO
from usecases.user.list_users.list_users_dto import ListUsersOutputDTO
from usecases.user.update_user.update_user_dto import UpdateUserOutputDTO


def _pydantic_to_dict(obj: Any) -> dict:
    # Pydantic v2: model_dump; v1: dict
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    # fallback
    return dict(obj)


def _normalize_roles(roles: Optional[Iterable[str]]) -> Optional[List[str]]:
    if roles is None:
        return None
    # ordenar para ficar estável no output
    return sorted([str(r) for r in roles])


class UserPresenter:
    @singledispatchmethod
    @staticmethod
    def toJSON(user_dto) -> dict:
        raise NotImplementedError("Unsupported type")

    @toJSON.register
    @staticmethod
    def _(user_dto: findUserByIdOutputDTO) -> dict:
        tasks = []
        for t in getattr(user_dto, "tasks", []) or []:
            tasks.append(_pydantic_to_dict(t))

        return {
            "id": str(user_dto.id),
            "name": user_dto.name,
            "email": str(getattr(user_dto, "email", "")) if getattr(user_dto, "email", None) is not None else None,
            "is_active": getattr(user_dto, "is_active", None),
            "roles": _normalize_roles(getattr(user_dto, "roles", None)),
            "tasks": tasks,
            "pending_tasks": user_dto.pending_tasks,
        }

    @toJSON.register
    @staticmethod
    def _(user_dto: AddUserOutputDTO) -> dict:
        return {
            "id": str(user_dto.id),
            "name": user_dto.name,
            "email": str(getattr(user_dto, "email", "")) if getattr(user_dto, "email", None) is not None else None,
            "is_active": getattr(user_dto, "is_active", None),
            "roles": _normalize_roles(getattr(user_dto, "roles", None)),
        }

    @toJSON.register
    @staticmethod
    def _(user_dto: UpdateUserOutputDTO) -> dict:
        return {
            "id": str(user_dto.id),
            "name": user_dto.name,
            "email": str(getattr(user_dto, "email", "")) if getattr(user_dto, "email", None) is not None else None,
            "is_active": getattr(user_dto, "is_active", None),
            "roles": _normalize_roles(getattr(user_dto, "roles", None)),
        }

    @toJSON.register
    @staticmethod
    def _(user_dto: ListUsersOutputDTO) -> list:
        # Importante: não incluir hashed_password
        result = []
        for user in user_dto.users:
            result.append(
                {
                    "id": str(user.id),
                    "name": user.name,
                    "email": str(getattr(user, "email", "")) if getattr(user, "email", None) is not None else None,
                    "is_active": getattr(user, "is_active", None),
                    "roles": _normalize_roles(getattr(user, "roles", None)),
                }
            )
        return result

    @singledispatchmethod
    @staticmethod
    def toXml(user_dto) -> str:
        raise NotImplementedError("Unsupported type")

    @toXml.register
    @staticmethod
    def _(user_dto: findUserByIdOutputDTO) -> str:
        user_data = ET.Element("user")
        ET.SubElement(user_data, "id").text = str(user_dto.id)
        ET.SubElement(user_data, "name").text = str(user_dto.name)

        email = getattr(user_dto, "email", None)
        if email is not None:
            ET.SubElement(user_data, "email").text = str(email)

        is_active = getattr(user_dto, "is_active", None)
        if is_active is not None:
            ET.SubElement(user_data, "is_active").text = str(is_active)

        roles = getattr(user_dto, "roles", None)
        if roles is not None:
            roles_el = ET.SubElement(user_data, "roles")
            for r in _normalize_roles(roles) or []:
                ET.SubElement(roles_el, "role").text = str(r)

        for task in getattr(user_dto, "tasks", []) or []:
            task_element = ET.SubElement(user_data, "task")
            ET.SubElement(task_element, "id").text = str(task.id)
            ET.SubElement(task_element, "title").text = str(task.title)
            ET.SubElement(task_element, "description").text = str(task.description)
            ET.SubElement(task_element, "completed").text = str(task.completed)

        ET.SubElement(user_data, "pending_tasks").text = str(user_dto.pending_tasks)
        return ET.tostring(user_data, encoding="unicode")

    @toXml.register
    @staticmethod
    def _(user_dto: AddUserOutputDTO) -> str:
        user_data = ET.Element("user")
        ET.SubElement(user_data, "id").text = str(user_dto.id)
        ET.SubElement(user_data, "name").text = str(user_dto.name)

        email = getattr(user_dto, "email", None)
        if email is not None:
            ET.SubElement(user_data, "email").text = str(email)

        is_active = getattr(user_dto, "is_active", None)
        if is_active is not None:
            ET.SubElement(user_data, "is_active").text = str(is_active)

        roles = getattr(user_dto, "roles", None)
        if roles is not None:
            roles_el = ET.SubElement(user_data, "roles")
            for r in _normalize_roles(roles) or []:
                ET.SubElement(roles_el, "role").text = str(r)

        return ET.tostring(user_data, encoding="unicode")

    @toXml.register
    @staticmethod
    def _(user_dto: UpdateUserOutputDTO) -> str:
        user_data = ET.Element("user")
        ET.SubElement(user_data, "id").text = str(user_dto.id)
        ET.SubElement(user_data, "name").text = str(user_dto.name)

        email = getattr(user_dto, "email", None)
        if email is not None:
            ET.SubElement(user_data, "email").text = str(email)

        is_active = getattr(user_dto, "is_active", None)
        if is_active is not None:
            ET.SubElement(user_data, "is_active").text = str(is_active)

        roles = getattr(user_dto, "roles", None)
        if roles is not None:
            roles_el = ET.SubElement(user_data, "roles")
            for r in _normalize_roles(roles) or []:
                ET.SubElement(roles_el, "role").text = str(r)

        return ET.tostring(user_data, encoding="unicode")

    @toXml.register
    @staticmethod
    def _(user_dto: ListUsersOutputDTO) -> str:
        data = ET.Element("data")
        for user in user_dto.users:
            user_element = ET.SubElement(data, "user")
            ET.SubElement(user_element, "id").text = str(user.id)
            ET.SubElement(user_element, "name").text = str(user.name)

            email = getattr(user, "email", None)
            if email is not None:
                ET.SubElement(user_element, "email").text = str(email)

            is_active = getattr(user, "is_active", None)
            if is_active is not None:
                ET.SubElement(user_element, "is_active").text = str(is_active)

            roles = getattr(user, "roles", None)
            if roles is not None:
                roles_el = ET.SubElement(user_element, "roles")
                for r in _normalize_roles(roles) or []:
                    ET.SubElement(roles_el, "role").text = str(r)

        return ET.tostring(data, encoding="unicode")