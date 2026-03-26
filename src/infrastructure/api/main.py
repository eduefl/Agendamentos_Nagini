from contextlib import asynccontextmanager

from fastapi import FastAPI

from infrastructure.api.database import SessionLocal, create_tables
from infrastructure.api.routers import task_routers, user_routers
from infrastructure.user.sqlalchemy.seed_roles import seed_roles


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
app.include_router(task_routers.router)

