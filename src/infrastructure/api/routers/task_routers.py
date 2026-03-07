from usecases.task.create_task_usecase import CreateTaskUseCase
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from usecases.task.create_task_dto import CreateTaskIpnutDTO
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from infrastructure.api.database import get_session


router = APIRouter(prefix = "/tasks", tags=["Tasks"])

# criar tarefas
# http:://localhost:8000/tasks
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(request: CreateTaskIpnutDTO, session: Session = Depends(get_session)):
	
	try:
		task_repository = taskRepository(session = session)
		usecase = CreateTaskUseCase(task_repository = task_repository)
		output =  usecase.execute(input = request) 
		# output_json = TaskPresenter.toJSON(output)
		# output_xml = TaskPresenter.toXml(output)
		return output
	except HTTPException as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))