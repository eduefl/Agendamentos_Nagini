from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from domain.user.user_exceptions import UserNotFoundError
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
from usecases.user.update_user.update_user_dto import UpdateUserDataDTO, UpdateUserInputDTO
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
		raise e

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
	except UserNotFoundError as e:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(e),  # "User with id ... not found"
		)	
	except HTTPException as e:
		raise e

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
		raise e
	
# alterar o nome do usuario
# http:://localhost:8000/users/{user_id}
@router.put("/{user_id}",status_code=status.HTTP_200_OK)
# o UpdateUserDataDTO recebe apenas os campos que podem ser atualizados, 
# enquanto o UpdateUserInputDTO inclui o campo id para identificar qual usuário atualizar. 
# Assim, mantemos a separação entre os dados de entrada e a estrutura completa da entidade.
def update_user(user_id: UUID, request: UpdateUserDataDTO, session: Session = Depends(get_session)):
	try:
		user_repository = userRepository(session = session)
		usecase = updateUserUsecase(user_repository = user_repository)
		input_dto = UpdateUserInputDTO(id=user_id, **request.dict()) # o **request.dict() 
																		# é um truque para pegar 
																		# os campos do UpdateUserDataDTO e passar como argumentos para o
																		#  UpdateUserInputDTO, junto com o id que vem da URL.
																		#  Assim, criamos um DTO completo para chamar o usecase. 
																		# request.dict() retorna um dict (ex.: {"name": "Eduardo"}).
																		# O ** faz o desempacotamento desse dict em argumentos nomeados.
																		# Observação sobre versão do Pydantic
																		# Pydantic v2: model_dump()
																		# Pydantic v1: dict()
		output = usecase.execute( input_dto = input_dto) # aqui criamos o input_dto completo para passar para o usecase, que precisa do id e dos campos atualizaveis.
		output_json = UserPresenter.toJSON(output)
		output_xml = UserPresenter.toXml(output)
		return {"json": output_json, "xml": output_xml}
	except UserNotFoundError as e:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(e),  # "User with id ... not found"
		)	
	except HTTPException as e:
		raise e

"""
# Fazer o processo de inclusao de tarefas
Criar Entidade
	Init
	Validate
Criar interface repositorio 
	entidade_repository_interface

Criar caso de uso e os DTOs

Implementar o repositorio usando SQLAlchemy e os modelos em infra estrutura

criar rotas na api

criar os presenters 
"""
