from typing import Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.auth import User
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import user_permissions


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing authentication token", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM.strip().upper()])
        user_id = UUID(str(payload.get("sub")))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = AuthRepository(db).find_user_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_permission(permission_name: str) -> Callable:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if permission_name not in user_permissions(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission required: {permission_name}")
        return user

    return dependency