from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.auth import Permission, Role, User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_user_by_email(self, email: str) -> User | None:
        statement = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.email == email)
        return self.db.scalar(statement)

    def find_user_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id)
        return self.db.scalar(statement)

    def find_role_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def commit(self) -> None:
        self.db.commit()

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).order_by(User.created_at.desc())).unique().all())

    def list_roles(self) -> list[Role]:
        return list(self.db.scalars(select(Role).options(selectinload(Role.permissions)).order_by(Role.name)).all())

    def list_permissions(self) -> list[Permission]:
        return list(self.db.scalars(select(Permission).order_by(Permission.name)).all())

    def find_user(self, user_id: UUID) -> User | None:
        return self.find_user_by_id(user_id)

    def find_role(self, role_id: UUID) -> Role | None:
        return self.db.scalar(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id))

    def find_permission(self, permission_id: UUID) -> Permission | None:
        return self.db.scalar(select(Permission).where(Permission.id == permission_id))

    def count_active_admins(self) -> int:
        return int(self.db.scalar(select(func.count(User.id)).join(User.roles).where(Role.name == "ADMIN", User.is_active.is_(True))) or 0)

    def count_role_users(self, role_id: UUID) -> int:
        return int(self.db.scalar(select(func.count(User.id)).join(User.roles).where(Role.id == role_id)) or 0)

    def count_permission_roles(self, permission_id: UUID) -> int:
        return int(self.db.scalar(select(func.count(Role.id)).join(Role.permissions).where(Permission.id == permission_id)) or 0)

    def delete(self, entity) -> None:
        self.db.delete(entity)