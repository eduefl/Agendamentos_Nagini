from fastapi import Depends, HTTPException, status

from domain.user.user_entity import User
from infrastructure.api.security.get_current_user import get_current_user


def require_prestador(
    current_user: User = Depends(get_current_user),
) -> User:
    roles = {role.lower() for role in current_user.roles}

    if "prestador" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas usuários com perfil prestador podem acessar esta rota",
        )

    return current_user
