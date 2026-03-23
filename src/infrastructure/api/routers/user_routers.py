from uuid import UUID

from infrastructure.api.factories.make_add_client_usecase import make_add_client_usecase
from usecases.user.add_user.add_prestador_dto import AddPrestadorInputDTO
from usecases.user.add_user.add_prestador_usecase import AddPrestadorUseCase
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from domain.user.user_exceptions import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    RolesRequiredError,
    UserNotFoundError,
)
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


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_user(request: AddUserInputDTO, session: Session = Depends(get_session)):
    try:
        user_repository = userRepository(session=session)
        password_hasher = PasslibPasswordHasher()

        usecase = AddUserUseCase(
            user_repository=user_repository,
            password_hasher=password_hasher,
        )

        # AddUserInputDTO agora deve ter request.role
        output = usecase.execute(input=request)

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RolesRequiredError as e:
        # normalmente seria 422, mas como é regra de domínio, 400 também é aceitável.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RoleNotFoundError as e:
        # role inválida/inesperada no input
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def add_client(request: AddClientInputDTO, session: Session = Depends(get_session)):
    try:

        usecase = make_add_client_usecase(session)

        output = usecase.execute(input=request)

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RolesRequiredError as e:
        # normalmente seria 422, mas como é regra de domínio, 400 também é aceitável.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RoleNotFoundError as e:
        # role inválida/inesperada no input
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e

@router.post("/providers", status_code=status.HTTP_201_CREATED)
def add_prestador(request: AddPrestadorInputDTO, session: Session = Depends(get_session)):   
    try:
        user_repository = userRepository(session=session)
        password_hasher = PasslibPasswordHasher()

        usecase = AddPrestadorUseCase(
            user_repository=user_repository,
            password_hasher=password_hasher,
        )

        output = usecase.execute(input=request)

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RolesRequiredError as e:
        # normalmente seria 422, mas como é regra de domínio, 400 também é aceitável.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RoleNotFoundError as e:
        # role inválida/inesperada no input
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e

@router.get("/{user_id}", status_code=status.HTTP_200_OK)
def find_user_by_id(user_id: UUID, session: Session = Depends(get_session)):
    try:
        user_repository = userRepository(session=session)
        task_repository = taskRepository(session=session)

        usecase = FindUserByIdUseCase(
            user_repository=user_repository,
            task_repository=task_repository,
        )
        output = usecase.execute(input=findUserByIdInputDTO(id=user_id))

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as e:
        raise e


@router.get("/", status_code=status.HTTP_200_OK)
def list_users(session: Session = Depends(get_session)):
    try:
        user_repository = userRepository(session=session)
        usecase = ListUsersUseCase(user_repository=user_repository)

        output = usecase.execute(input=ListUsersInputDTO())

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except HTTPException as e:
        raise e


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def update_user(
    user_id: UUID,
    request: UpdateUserDataDTO,
    session: Session = Depends(get_session),
):
    try:
        user_repository = userRepository(session=session)
        usecase = updateUserUsecase(user_repository=user_repository)

        # # Pydantic v2: model_dump / v1: dict
        # data = request.model_dump() if hasattr(request, "model_dump") else request.dict()

        # input_dto = UpdateUserInputDTO(id=user_id, **data)
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

        output = usecase.execute(input=input_dto)

        output_json = UserPresenter.toJSON(output)
        output_xml = UserPresenter.toXml(output)
        return {"json": output_json, "xml": output_xml}

    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except HTTPException as e:
        raise e