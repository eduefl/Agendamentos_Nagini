from infrastructure.api.database import create_tables
from fastapi import FastAPI
from infrastructure.api.routers import user_routers	
from infrastructure.api.routers import task_routers

app = FastAPI()

app.include_router(user_routers.router)
app.include_router( task_routers.router)

create_tables() 