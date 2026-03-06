from infrastructure.api.database import create_tables
from fastapi import FastAPI
from infrastructure.api.routers import user_routers	

app = FastAPI()

app.include_router(user_routers.router)

create_tables() 