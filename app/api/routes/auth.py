from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.auth import User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import AuthUserResponse, LoginRequest, LoginResponse
from app.services.auth_service import authenticate, create_access_token, user_permissions, user_roles


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def to_user_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(id=user.id, email=user.email, full_name=user.full_name, roles=user_roles(user), permissions=user_permissions(user))


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(AuthRepository(db), request.email, request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return LoginResponse(access_token=create_access_token(user.id), token_type="bearer", user=to_user_response(user))


@router.get("/me", response_model=AuthUserResponse)
def me(user: User = Depends(get_current_user)):
    return to_user_response(user)