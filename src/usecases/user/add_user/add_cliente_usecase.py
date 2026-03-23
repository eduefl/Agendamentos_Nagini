import secrets
from uuid import uuid4

from domain.notification.email_sender_interface import EmailSenderInterface
from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_entity import User
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.user.add_user.add_cliente_dto import AddClientInputDTO, AddClientOutputDTO

class AddClientUseCase(UseCaseInterface):
    def __init__(
        self,
        user_repository: userRepositoryInterface,
        password_hasher: PasswordHasherInterface,
        email_sender: EmailSenderInterface,          # NOVO parâmetro        
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.email_sender = email_sender             # Armazena para uso        

    def execute(self, input: AddClientInputDTO) -> AddClientOutputDTO:
        # 1-Crio o hash da senha usando o PasswordHasherInterface com base na senha
        hashed_password = self.password_hasher.hash(input.password)
        # 2-Cria uma instância de User usando os dados do input e o hash da senha
        user = User(
            id=uuid4(),
            name=input.name,
            email=str(input.email),
            hashed_password=hashed_password,
            is_active=False,
            roles={"cliente"}
        )

        # 3-Salva o usuário usando o userRepositoryInterface
        try:
            # activation_code = str(uuid4())[:8]  # ou gere conforme sua política
            activation_code = secrets.token_hex(4)  # 8 chars hex
            self.email_sender.send_activation_email(user.email, activation_code)
        except Exception as e:
            raise e

        self.user_repository.add_user(user=user)
                
        # 4-Retorna um AddClientOutputDTO com os dados do usuário criado (exceto hashed_password)
        return AddClientOutputDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            roles=sorted(list(user.roles)),            
        )