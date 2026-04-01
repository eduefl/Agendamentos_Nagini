from fastapi import Depends, HTTPException, status

from domain.user.user_entity import User
from infrastructure.api.security.get_current_user import get_current_user


def require_cliente(
    current_user: User = Depends(get_current_user),
) -> User:
    roles = {role.lower() for role in current_user.roles}

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo não pode acessar esta operação",
        )
    if "cliente" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas usuários com perfil cliente podem acessar esta rota",
        )

    return current_user
