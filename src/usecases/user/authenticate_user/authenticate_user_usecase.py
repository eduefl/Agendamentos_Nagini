
from domain.security.token_service_dto import CreateAccessTokenDTO
from domain.__seedwork.use_case_interface import UseCaseInterface
from domain.security.token_service_interface import TokenServiceInterface
from domain.user.user_exceptions import InvalidCredentialsError, UserNotFoundError
from usecases.user.authenticate_user.authenticate_user_dto import AuthenticateUserInputDTO, AuthenticateUserOutputDTO
from domain.security.password_hasher_interface import PasswordHasherInterface
from domain.user.user_repository_interface import userRepositoryInterface


class AuthenticateUserUseCase(UseCaseInterface):
    def __init__(
        self,
        user_repository: userRepositoryInterface,
        password_hasher: PasswordHasherInterface,
        tokenService: TokenServiceInterface
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.tokenService = tokenService

    def execute(self, input: AuthenticateUserInputDTO)-> AuthenticateUserOutputDTO:
        try:
            user = self.user_repository.find_user_by_email(email = input.email)
        except UserNotFoundError as exc:
            raise InvalidCredentialsError()  from exc
        
        if not user.is_active:
            raise InvalidCredentialsError()# No login ativo, o usuário deve estar ativo para autenticar. 
                                                #Se o usuário não estiver ativo, isso pode indicar que ele ainda não ativou sua conta ou que a conta foi desativada por algum motivo. 
                                                # Portanto, é apropriado lançar um erro de credenciais inválidas para evitar fornecer informações adicionais sobre o status da conta do usuário.

        if not self.password_hasher.verify(password= input.password, hashed_password = user.hashed_password):
            raise InvalidCredentialsError()
        data = CreateAccessTokenDTO(
            sub=user.id, 
            email=user.email, 
            roles=sorted(map(str, user.roles)) if user.roles else []
        )

        output = self.tokenService.create_access_token(data=data) 

        return AuthenticateUserOutputDTO(
            access_token=output,
            token_type="bearer"
        )

