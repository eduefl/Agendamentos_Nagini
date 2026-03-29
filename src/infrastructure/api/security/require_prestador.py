from fastapi import Depends

from domain.__seedwork.exceptions import ForbiddenError
from domain.user.user_entity import User
from infrastructure.api.security.get_current_user import get_current_user


def require_prestador(
    current_user: User = Depends(get_current_user),
) -> User:
    roles = {role.name.lower() for role in current_user.roles}

    if "prestador" not in roles:
        raise ForbiddenError("Apenas usuários com perfil prestador podem acessar esta rota")

    return current_user