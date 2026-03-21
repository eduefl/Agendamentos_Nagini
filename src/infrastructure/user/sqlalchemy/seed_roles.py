from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from infrastructure.user.sqlalchemy.user_model import RoleModel

DEFAULT_ROLES = ["cliente", "prestador"]

def seed_roles(session: Session) -> None:
    existing = {name for (name,) in session.query(RoleModel.name).all()}

    for role_name in DEFAULT_ROLES:
        if role_name not in existing:
            session.add(RoleModel(name=role_name))

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # se ocorreu corrida (2 startups), ignora