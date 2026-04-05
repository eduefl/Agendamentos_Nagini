from infrastructure.api.routers._error_mapper import raise_http_from_error
from infrastructure.security.factories.make_token_service import make_token_service
from domain.security.token_service_dto import TokenPayloadDTO
from fastapi import Depends
from infrastructure.api.security.oauth2 import oauth2_scheme


def get_current_token_payload(
    token: str = Depends(oauth2_scheme),
) -> TokenPayloadDTO:
    try:
        token_service = make_token_service()
        return token_service.decode_token(token)
    except Exception as e:
        raise_http_from_error(e)