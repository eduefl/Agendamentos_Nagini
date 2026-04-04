from typing import Optional
from uuid import UUID

from infrastructure.user.sqlalchemy.user_model import RoleModel, UserModel, user_roles
from domain.service.eligible_provider_read_model import EligibleProviderReadModel
from domain.service.provider_service_list_item_read_model import ProviderServiceListItem
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from sqlalchemy.orm import Session

from domain.service.provider_service_entity import ProviderService
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)


class ProviderServiceRepository(ProviderServiceRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def create_provider_service(self, provider_service: ProviderService) -> None:
        provider_service_model = ProviderServiceModel(
            id=provider_service.id,
            provider_id=provider_service.provider_id,
            service_id=provider_service.service_id,
            price=provider_service.price,
            active=provider_service.active,
            created_at=provider_service.created_at,
        )
        self.session.add(provider_service_model)
        self.session.flush()

    def find_by_provider_and_service(
        self,
        provider_id: UUID,
        service_id: UUID,
    ) -> Optional[ProviderService]:
        provider_service_in_db = (
            self.session.query(ProviderServiceModel)
            .filter(
                ProviderServiceModel.provider_id == provider_id,
                ProviderServiceModel.service_id == service_id,
            )
            .first()
        )

        if not provider_service_in_db:
            return None

        return self._to_entity(provider_service_in_db)

    def list_by_provider_id(self, provider_id: UUID) -> list[ProviderServiceListItem]:
        rows = (
            self.session.query(ProviderServiceModel, ServiceModel)
            .join(ServiceModel, ServiceModel.id == ProviderServiceModel.service_id)
            .filter(ProviderServiceModel.provider_id == provider_id)
            .all()
        )

        return [
            ProviderServiceListItem(
                id=provider_service.id,
                provider_id=provider_service.provider_id,
                service_id=provider_service.service_id,
                service_name=service.name,
                service_description=service.description,
                price=provider_service.price,
                active=provider_service.active,
                created_at=provider_service.created_at,
            )
            for provider_service, service in rows
        ]


    def find_by_id(self, provider_service_id: UUID) -> Optional[ProviderService]:
        provider_service_in_db = (
            self.session.query(ProviderServiceModel)
            .filter(ProviderServiceModel.id == provider_service_id)
            .first()
        )

        if provider_service_in_db is None:
            return None

        return self._to_entity(provider_service_in_db)


    def update(self, provider_service: ProviderService) -> ProviderService:
        provider_service_in_db = (
            self.session.query(ProviderServiceModel)
            .filter(ProviderServiceModel.id == provider_service.id)
            .first()
        )

        provider_service_in_db.active = provider_service.active

        self.session.commit()
        self.session.refresh(provider_service_in_db)

        return self._to_entity(provider_service_in_db)


    def list_eligible_providers_by_service_id(
        self, service_id: UUID
    ) -> list[EligibleProviderReadModel]:
        rows = (
            self.session.query(ProviderServiceModel, UserModel)
            .join(UserModel, UserModel.id == ProviderServiceModel.provider_id)
            .join(user_roles, user_roles.c.user_id == UserModel.id)
            .join(RoleModel, RoleModel.id == user_roles.c.role_id)
            .filter(
                ProviderServiceModel.service_id == service_id,
                ProviderServiceModel.active == True,
                UserModel.is_active == True,
                RoleModel.name == "prestador",
            )
            .all()
        )
        return [
            EligibleProviderReadModel(
                provider_id=ps.provider_id,
                provider_name=user.name,
                provider_email=user.email,
                provider_service_id=ps.id,
                service_id=ps.service_id,
                price=ps.price,
            )
            for ps, user in rows
        ]

    @staticmethod
    def _to_entity(model: ProviderServiceModel) -> ProviderService:
        return ProviderService(
            id=model.id,
            provider_id=model.provider_id,
            service_id=model.service_id,
            price=model.price,
            active=model.active,
            created_at=model.created_at,
        )
