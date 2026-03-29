from infrastructure.api.security.get_current_token import get_current_token_payload
from domain.security.token_service_dto import TokenPayloadDTO
from domain.user.user_entity import User
from infrastructure.api.database import get_session
from infrastructure.user.sqlalchemy.user_repository import userRepository
from fastapi import Depends

from sqlalchemy.orm import Session


def get_current_user(
    token_payload: TokenPayloadDTO = Depends(get_current_token_payload),
    session: Session = Depends(get_session),
) -> User:
    user_repository = userRepository(session=session)
    user = user_repository.find_user_by_id(token_payload.sub)
    return user
