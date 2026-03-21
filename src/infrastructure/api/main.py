from fastapi import FastAPI

from infrastructure.api.database import create_tables, SessionLocal
from infrastructure.api.routers import user_routers, task_routers
from infrastructure.user.sqlalchemy.seed_roles import seed_roles

app = FastAPI()

app.include_router(user_routers.router)
app.include_router(task_routers.router)

@app.on_event("startup")
def on_startup():
    # 1) garante tabelas
    create_tables()

    # 2) garante roles fixas
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()

        