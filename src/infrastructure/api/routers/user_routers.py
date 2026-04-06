from uuid import UUID
from fastapi.security import OAuth2PasswordRequestForm
from usecases.user.authenticate_user.authenticate_user_dto import AuthenticateUserInputDTO, AuthenticateUserOutputDTO
from infrastructure.api.factories.make_add_client_usecase import make_add_client_usecase
from infrastructure.api.factories.make_add_provider_usecase import make_add_provider_usecase
from infrastructure.api.factories.make_authenticate_user_usecase import make_authenticate_user_usecase

from infrastructure.api.routers._error_mapper import raise_http_from_error
from usecases.user.activate_user.activate_user_usecase import ActivateUserUseCase
from usecases.user.activate_user.activate_user_dto import ActivateUserInputDTO
from usecases.user.add_user.add_prestador_dto import AddPrestadorInputDTO
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from infrastructure.api.database import get_session
from infrastructure.presenters.user_presenter import UserPresenter
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.task.sqlalchemy.task_repository import taskRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from usecases.user.add_user.add_user_dto import AddUserInputDTO
from usecases.user.add_user.add_user_usecase import AddUserUseCase
from usecases.user.find_user_by_id.find_user_by_id_dto import findUserByIdInputDTO
from usecases.user.find_user_by_id.find_user_by_id_usecase import FindUserByIdUseCase
from usecases.user.list_users.list_users_dto import ListUsersInputDTO
from usecases.user.list_users.list_users_usecase import ListUsersUseCase
from usecases.user.update_user.update_user_dto import UpdateUserDataDTO, UpdateUserInputDTO
from usecases.user.update_user.update_user_usecase import updateUserUsecase

router = APIRouter(prefix="/users", tags=["Users"])


# @router.post("/", status_code=status.HTTP_201_CREATED)
# def add_user(request: AddUserInputDTO, session: Session = Depends(get_session)):
#     try:
#         user_repository = userRepository(session=session)
#         password_hasher = PasslibPasswordHasher()

#         usecase = AddUserUseCase(
#             user_repository=user_repository,
#             password_hasher=password_hasher,
#         )

#         # AddUserInputDTO agora deve ter request.role
#         output = usecase.execute(input=request)

#         output_json = UserPresenter.toJSON(output)
#         output_xml = UserPresenter.toXml(output)
#         return {"json": output_json, "xml": output_xml}

#     except Exception as e:
#         raise_http_from_error(e)


@router.get("/", status_code=status.HTTP_200_OK)
def list_users(session: Session = Depends(get_session)):
    try:
        user_repository = userRepository(session=session)
        usecase = ListUsersUseCase(user_repository=user_repository)

        output = usecase.execute(input=ListUsersInputDTO())

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except Exception as e:
        raise_http_from_error(e)


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def add_client(request: AddClientInputDTO, session: Session = Depends(get_session)):
    try:

        usecase = make_add_client_usecase(session)

        output = usecase.execute(input=request)

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except Exception as e:
        raise_http_from_error(e)

@router.post("/providers", status_code=status.HTTP_201_CREATED)
def add_prestador(request: AddPrestadorInputDTO, session: Session = Depends(get_session)):   
    try:
        usecase = make_add_provider_usecase(session)

        output = usecase.execute(input=request)

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except Exception as e:
        raise_http_from_error(e)

# @router.get("/{user_id}", status_code=status.HTTP_200_OK)
# def find_user_by_id(user_id: UUID, session: Session = Depends(get_session)):
#     try:
#         user_repository = userRepository(session=session)
#         task_repository = taskRepository(session=session)

#         usecase = FindUserByIdUseCase(
#             user_repository=user_repository,
#             task_repository=task_repository,
#         )
#         output = usecase.execute(input=findUserByIdInputDTO(id=user_id))

#         output_json = UserPresenter.toJSON(output)
#         output_xml = UserPresenter.toXml(output)
#         return {"json": output_json, "xml": output_xml}

#     except Exception as e:
#         raise_http_from_error(e)




# @router.put("/{user_id}", status_code=status.HTTP_200_OK)
# def update_user(
#     user_id: UUID,
#     request: UpdateUserDataDTO,
#     session: Session = Depends(get_session),
# ):
#     try:
#         user_repository = userRepository(session=session)
#         usecase = updateUserUsecase(user_repository=user_repository)

#         # # Pydantic v2: model_dump / v1: dict
#         # data = request.model_dump() if hasattr(request, "model_dump") else request.dict()

#         # input_dto = UpdateUserInputDTO(id=user_id, **data)
#         input_dto = UpdateUserInputDTO(id=user_id, **request.dict()) # o **request.dict() 
# 																		# é um truque para pegar 
# 																		# os campos do UpdateUserDataDTO e passar como argumentos para o
# 																		#  UpdateUserInputDTO, junto com o id que vem da URL.
# 																		#  Assim, criamos um DTO completo para chamar o usecase. 
# 																		# request.dict() retorna um dict (ex.: {"name": "Eduardo"}).
# 																		# O ** faz o desempacotamento desse dict em argumentos nomeados.
# 																		# Observação sobre versão do Pydantic
# 																		# Pydantic v2: model_dump()
# 																		# Pydantic v1: dict()

#         output = usecase.execute(input=input_dto)

#         output_json = UserPresenter.toJSON(output)
#         output_xml = UserPresenter.toXml(output)
#         return {"json": output_json, "xml": output_xml}

#     except Exception as e:
#         raise_http_from_error(e)
    
@router.post("/activate/", status_code=status.HTTP_200_OK)
def activate_user(request: ActivateUserInputDTO, 
                  session: Session = Depends(get_session)):
    try:
        user_repository = userRepository(session=session)
        password_hasher = PasslibPasswordHasher()

        usecase = ActivateUserUseCase(
            user_repository=user_repository,
            password_hasher=password_hasher,
        )

        output = usecase.execute(input=request)

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}
    except Exception as e:
        raise_http_from_error(e)


@router.post("/login", response_model=AuthenticateUserOutputDTO, status_code=status.HTTP_200_OK)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    try:
        usecase = make_authenticate_user_usecase(session)

        input_dto = AuthenticateUserInputDTO(
            email=form_data.username,   # aqui o "username" do OAuth2 vira seu email
            password=form_data.password,
        )

        output = usecase.execute(input=input_dto)
        return output
    except Exception as e:
        raise_http_from_error(e)