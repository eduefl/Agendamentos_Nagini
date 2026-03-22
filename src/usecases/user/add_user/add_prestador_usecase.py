from uuid import uuid4

from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_entity import User
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.add_user.add_prestador_dto import AddPrestadorInputDTO, AddPrestadorOutputDTO

class AddPrestadorUseCase(UseCaseInterface):
    def __init__(
        self,
        user_repository: userRepositoryInterface,
        password_hasher: PasswordHasherInterface,
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    def execute(self, input: AddPrestadorInputDTO) -> AddPrestadorOutputDTO:
        # 1-Crio o hash da senha usando o PasswordHasherInterface com base na senha
        hashed_password = self.password_hasher.hash(input.password)
        # 2-Cria uma instância de User usando os dados do input e o hash da senha
        user = User(
            id=uuid4(),
            name=input.name,
            email=str(input.email),
            hashed_password=hashed_password,
            is_active=False,
            roles={"prestador"}
        )

        # 3-Salva o usuário usando o userRepositoryInterface
        self.user_repository.add_user(user=user)

        # 4-Retorna um AddPrestadorOutputDTO com os dados do usuário criado (exceto hashed_password)
        return AddPrestadorOutputDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            roles=sorted(list(user.roles)),            
        )