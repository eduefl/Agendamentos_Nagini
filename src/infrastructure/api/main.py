from contextlib import asynccontextmanager

from infrastructure.api.routers import provider_service_request_routers
from fastapi import FastAPI

from infrastructure.api.database import SessionLocal, create_tables
from infrastructure.api.routers import (
    user_routers,
    provider_service_routers,
    service_request_routers,
    service_routers,
)
from infrastructure.api.routers import provider_schedule_router

from infrastructure.user.sqlalchemy.seed_roles import seed_roles

# importa os models para registrar no SQLAlchemy
from infrastructure.user.sqlalchemy.user_model import UserModel, RoleModel
from infrastructure.service.sqlalchemy.service_model import ServiceModel
from infrastructure.service.sqlalchemy.provider_service_model import (
    ProviderServiceModel,
)
from infrastructure.service_request.sqlalchemy.service_request_model import (
    ServiceRequestModel,
)
from infrastructure.payment.sqlalchemy.payment_attempt_model import PaymentAttemptModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) garante tabelas
    create_tables()

    # 2) garante roles fixas
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(user_routers.router)
app.include_router(service_routers.router)
app.include_router(provider_service_routers.router)

app.include_router(service_request_routers.router)
app.include_router(provider_service_request_routers.router)
app.include_router(provider_schedule_router.router)
