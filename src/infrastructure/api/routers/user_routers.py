from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from usecases.user.add_user.add_user_dto import AddUserInputDTO
from sqlalchemy.orm import Session
from infrastructure.api.database import get_session
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.add_user.add_user_usecase import AddUserUseCase
from usecases.user.find_user_by_id.find_user_by_id_usecase import FindUserByIdUseCase
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdInputDTO
from usecases.user.list_users.list_users_usecase import ListUsersUseCase
from usecases.user.list_users.list_users_dto import ListUsersInputDTO
from usecases.user.update_user.update_user_usecase import updateUserUsecase
from usecases.user.update_user.update_user_dto import UpdateUserInputDTO
from infrastructure.presenters.user_presenter import UserPresenter

router = APIRouter(prefix = "/users", tags=["Users"])
# Adcionar Usuarios
# http:://localhost:8000/users
@router.post("/", status_code=status.HTTP_201_CREATED)
def add_user(request: AddUserInputDTO, session: Session = Depends(get_session)):

	try:
		user_repository = userRepository(session = session)
		usecase = AddUserUseCase(user_repository = user_repository)
		output =  usecase.execute(input = request) 
		output_json = UserPresenter.toJSON(output)
		output_xml = UserPresenter.toXml(output)

		return {"json": output_json, "xml": output_xml}
	except HTTPException as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Consultar usuarios por ID
# http:://localhost:8000/users/{user_id}
@router.get("/{user_id}",status_code=status.HTTP_200_OK)
def find_user_by_id(user_id :UUID, session: Session = Depends(get_session)):
	try:
		user_repository = userRepository(session = session)
		usecase = FindUserByIdUseCase(user_repository = user_repository)
		output =  usecase.execute(input = findUserByIdInputDTO(id=user_id)) 
		output_json = UserPresenter.toJSON(output)
		output_xml = UserPresenter.toXml(output)

		return {"json": output_json, "xml": output_xml}
	except HTTPException as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Listar todos os usuarios
# http:://localhost:8000/users
@router.get("/",status_code=status.HTTP_200_OK)	
def list_users(session: Session = Depends(get_session)):
	try:
		user_repository = userRepository(session = session)
		usecase = ListUsersUseCase(user_repository = user_repository)
		output =  usecase.execute(input = ListUsersInputDTO()) 
		output_json = UserPresenter.toJSON(output)
		output_xml = UserPresenter.toXml(output)

		return {"json": output_json, "xml": output_xml}
	except HTTPException as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))		
	
# alterar o nome do usuario
# http:://localhost:8000/users/{user_id}
@router.put("/{user_id}",status_code=status.HTTP_200_OK)
# def add_user(request: AddUserInputDTO, session: Session = Depends(get_session)):
def update_user(request: UpdateUserInputDTO, session: Session = Depends(get_session)):
	try:
		user_repository = userRepository(session = session)
		usecase = updateUserUsecase(user_repository = user_repository)
		output = usecase.execute(input_dto = request) 
		output_json = UserPresenter.toJSON(output)
		output_xml = UserPresenter.toXml(output)
		return {"json": output_json, "xml": output_xml}
	except HTTPException as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Continuar aula clear architeture 2 --02:45:02