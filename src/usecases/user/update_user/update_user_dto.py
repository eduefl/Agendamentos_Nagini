from pydantic import BaseModel
from uuid import UUID

# input

# aqui fazemos um truque para termos um DTO para receber os campos atualizaveis e outro da entidade completa para chamarmos no execute 
# o UpdateUserDataDTO vai ter apenas os campos que podem ser atualizados, 
class UpdateUserDataDTO(BaseModel):
    name: str
    # no futuro: email: EmailStr, phone: str, etc.
#o UpdateUserInputDTO vai herdar do UpdateUserDataDTO e adicionar o campo id, que é necessário para identificar qual usuário atualizar. Assim, mantemos a separação entre os dados de entrada e a estrutura completa da entidade. 
class UpdateUserInputDTO(UpdateUserDataDTO):
	id: UUID
# output
class UpdateUserOutputDTO(BaseModel):
	id: UUID
	name: str