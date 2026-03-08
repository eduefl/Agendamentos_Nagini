from domain.user.user_exceptions import UserNotFoundError
from usecases.task.create_task_usecase import CreateTaskUseCase
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.create_task_dto import CreateTaskInputDTO
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from infrastructure.api.database import get_session


router = APIRouter(prefix = "/tasks", tags=["Tasks"])

# criar tarefas
# http:://localhost:8000/tasks
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(request: CreateTaskInputDTO, session: Session = Depends(get_session)):
	
	try:
		task_repository = taskRepository(session = session)
		user_repository = userRepository(session = session)		
		usecase = CreateTaskUseCase(task_repository = task_repository, user_repository = user_repository)
		output =  usecase.execute(input = request) 
		# output_json = TaskPresenter.toJSON(output)
		# output_xml = TaskPresenter.toXml(output)
		return output
	except UserNotFoundError as e:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(e),  # "User with id ... not found"
		)	
	except HTTPException as e:
		raise e
