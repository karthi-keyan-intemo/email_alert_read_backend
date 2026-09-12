from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings
from app.models.auth import User
from app.repositories.auth_repository import AuthRepository


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM.strip().upper())


def user_permissions(user: User) -> list[str]:
    return sorted({permission.name for role in user.roles for permission in role.permissions})


def user_roles(user: User) -> list[str]:
    return sorted({role.name for role in user.roles})


def authenticate(repository: AuthRepository, email: str, password: str) -> User | None:
    user = repository.find_user_by_email(normalize_email(email))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user