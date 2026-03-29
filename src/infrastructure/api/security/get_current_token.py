from infrastructure.security.factories.make_token_service import make_token_service
from domain.security.token_service_dto import TokenPayloadDTO
from fastapi import Depends
from infrastructure.api.security.oauth2 import oauth2_scheme


def get_current_token_payload(
    token: str = Depends(oauth2_scheme),
) -> TokenPayloadDTO:
    token_service = make_token_service()
    return token_service.decode_token(token)