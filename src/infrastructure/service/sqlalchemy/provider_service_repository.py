from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from domain.service.provider_service_entity import ProviderService
from domain.service.provider_service_repository_interface import (
    ProviderServiceRepositoryInterface,
)
from infrastructure.service.sqlalchemy.provider_service_model import ProviderServiceModel


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
        provider_id:UUID,
        service_id:UUID,
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


    def list_by_provider_id(self, provider_id: UUID) -> list[ProviderService]:
        providers_services_in_db = (
            self.session.query(ProviderServiceModel)
            .filter(ProviderServiceModel.provider_id == provider_id)
            .all()
        )

        return [self._to_entity(provider_service_in_db) for provider_service_in_db in providers_services_in_db]

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
