from abc import ABC, abstractmethod

from domain.security.token_service_dto import CreateAccessTokenDTO, TokenPayloadDTO



class TokenServiceInterface (ABC):
    @abstractmethod
    def create_access_token(self, data: CreateAccessTokenDTO) -> str:
        raise NotImplementedError

    @abstractmethod
    def decode_token(self, token: str) -> TokenPayloadDTO:
        raise NotImplementedError