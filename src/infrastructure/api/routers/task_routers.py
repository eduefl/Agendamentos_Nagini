from uuid import UUID
from usecases.task.mark_as_completed.mark_as_completed_dto import MarkAsCompletedInputDTO
from usecases.task.mark_as_completed.mark_as_completed_usecase import MarkAsCompletedUseCase
from usecases.task.list_tasks_from_user.list_tasks_from_user_dto import ListTasksFromUserInputDTO
from usecases.task.list_tasks_from_user.list_tasks_from_user_usecase import ListTasksFromUserUseCase
from usecases.task.delete_task.delete_task_dto import DeleteTaskInputDTO
from usecases.task.delete_task.delete_task_usecase import DeleteTaskUseCase
from usecases.task.update_task.update_task_usecase import UpdateTaskUseCase
from usecases.task.update_task.update_task_dto import UpdateTaskDataDTO, UpdateTaskInputDTO

from infrastructure.presenters.task_presenter import TaskPresenter
from usecases.task.create_task.create_task_usecase import CreateTaskUseCase
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.task.create_task.create_task_dto import CreateTaskInputDTO
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from infrastructure.api.database import get_session
from usecases.task.get_task_by_id.get_task_by_id_usecase import GetTaskByIdUseCase
from usecases.task.get_task_by_id.get_task_by_id_dto import getTaskByIdInputDTO
from infrastructure.api.routers._error_mapper import raise_http_from_error

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
		output_json = TaskPresenter.toJSON(output)
		output_xml = TaskPresenter.toXml(output)
		return {
			"json": output_json,
			"xml": output_xml
		}	
	except Exception as e:
		raise_http_from_error(e)
	
# Listar tarefas de um usuario
# http:://localhost:8000/tasks/user/{user_id}
@router.get("/user/{user_id}", status_code=status.HTTP_200_OK)
def list_tasks_from_user(user_id: UUID, session: Session = Depends(get_session)):
	try:
		task_repository = taskRepository(session = session)
		user_repository = userRepository(session = session)
		usecase = ListTasksFromUserUseCase(task_repository = task_repository , 
									 user_repository = user_repository)	
		input_dto = ListTasksFromUserInputDTO (user_id = user_id)
		output = usecase.execute(input_dto = input_dto)	
		output_json = TaskPresenter.toJSON(output)
		output_xml = TaskPresenter.toXml(output)
		return {"json": output_json, "xml": output_xml}
	except Exception as e:
		raise_http_from_error(e)


# Consultar tarefas por ID
# http:://localhost:8000/tasks/{task_id}
@router.get("/{task_id}",status_code=status.HTTP_200_OK)
def find_task_by_id(task_id :UUID, session: Session = Depends(get_session)):
	try:
		task_repository = taskRepository(session = session)
		usecase = GetTaskByIdUseCase(task_repository = task_repository)
		output =  usecase.execute(input = getTaskByIdInputDTO(id=task_id))
		output_json = TaskPresenter.toJSON(output)
		output_xml = TaskPresenter.toXml(output)

		return {"json": output_json, "xml": output_xml}
	except Exception as e:
		raise_http_from_error(e)
	
# Alterar Dados tarefa
# http:://localhost:8000/tasks/{task_id}
# para completar use /complete
@router.put("/{task_id}", status_code=status.HTTP_200_OK)
def update_task(task_id: UUID, request: UpdateTaskDataDTO, session: Session = Depends(get_session)):
	try:
		task_repository	= taskRepository(session = session)
		user_repository = userRepository(session = session)				
		usecase = UpdateTaskUseCase(task_repository = task_repository, user_repository = user_repository)
		input_dto = UpdateTaskInputDTO(id = task_id, **request.dict())
		output = usecase.execute(input_dto = input_dto)	
		output_json = TaskPresenter.toJSON(output)
		output_xml = TaskPresenter.toXml(output)
		return {"json": output_json, "xml": output_xml}
	except Exception as e:
		raise_http_from_error(e)

# Deletar tarefa
# http:://localhost:8000/tasks/{task_id}
@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: UUID, session: Session = Depends(get_session)):
	try:
		task_repository = taskRepository(session = session)
		usecase = DeleteTaskUseCase(task_repository = task_repository)	
		input_dto = DeleteTaskInputDTO (id = task_id)
		output = usecase.execute(input = input_dto)	
		output_json = TaskPresenter.toJSON(output)
		output_xml = TaskPresenter.toXml(output)
		return {"json": output_json, "xml": output_xml}
	except Exception as e:
		raise_http_from_error(e)

# CompletarTarefa
# http:://localhost:8000/tasks/complete/{task_id}
@router.put("/complete/{task_id}", status_code=status.HTTP_200_OK)
def complete_task(task_id: UUID, session: Session = Depends(get_session)):
	try:
		task_repository = taskRepository(session = session)
		usecase = MarkAsCompletedUseCase(task_repository = task_repository)
		input_dto = MarkAsCompletedInputDTO(id = task_id)
		output = usecase.execute(input = input_dto)	
		output_json = TaskPresenter.toJSON(output)
		output_xml = TaskPresenter.toXml(output)
		return {"json": output_json, "xml": output_xml}
	except Exception as e:
		raise_http_from_error(e)

