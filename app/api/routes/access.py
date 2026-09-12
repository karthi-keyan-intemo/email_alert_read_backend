from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.db.database import get_db
from app.models.auth import Permission, Role, User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import (
    PermissionCreateRequest, PermissionResponse, PermissionUpdateRequest,
    PasswordResetRequest, RoleCreateRequest, RoleResponse, RoleUpdateRequest,
    UserCreateRequest, UserResponse, UserUpdateRequest,
)
from app.services.access_service import AccessService
from app.services.auth_service import user_permissions, user_roles


router = APIRouter(prefix="/api", tags=["Access Management"])


def service(db: Session) -> AccessService:
    return AccessService(AuthRepository(db))


def error(exc: ValueError) -> HTTPException:
    message = str(exc)
    code = status.HTTP_404_NOT_FOUND if message.endswith("not found.") else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=message)


def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, full_name=user.full_name, roles=user_roles(user), permissions=user_permissions(user), is_active=user.is_active, created_at=user.created_at)


def role_response(role: Role) -> RoleResponse:
    return RoleResponse(id=role.id, name=role.name, description=role.description, permissions=sorted(permission.name for permission in role.permissions))


def permission_response(permission: Permission) -> PermissionResponse:
    return PermissionResponse(id=permission.id, name=permission.name, description=permission.description)


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    return [user_response(user) for user in service(db).list_users()]


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(request: UserCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: return user_response(service(db).create_user(request.email, request.full_name, request.password, request.role_ids))
    except ValueError as exc: raise error(exc) from exc


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    user = AuthRepository(db).find_user(user_id)
    if user is None: raise HTTPException(status_code=404, detail="User not found.")
    return user_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, request: UserUpdateRequest, db: Session = Depends(get_db), actor: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: return user_response(service(db).update_user(actor, user_id, request.email, request.full_name, request.role_ids, request.is_active))
    except ValueError as exc: raise error(exc) from exc


@router.delete("/users/{user_id}", status_code=204)
def deactivate_user(user_id: UUID, db: Session = Depends(get_db), actor: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: service(db).delete_user(actor, user_id)
    except ValueError as exc: raise error(exc) from exc


@router.post("/users/{user_id}/reset-password", status_code=204)
def reset_password(user_id: UUID, request: PasswordResetRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: service(db).reset_password(user_id, request.password)
    except ValueError as exc: raise error(exc) from exc


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    return [role_response(role) for role in service(db).list_roles()]


@router.post("/roles", response_model=RoleResponse, status_code=201)
def create_role(request: RoleCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: return role_response(service(db).create_role(request.name, request.description, request.permission_ids))
    except ValueError as exc: raise error(exc) from exc


@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    role = AuthRepository(db).find_role(role_id)
    if role is None: raise HTTPException(status_code=404, detail="Role not found.")
    return role_response(role)


@router.patch("/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: UUID, request: RoleUpdateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: return role_response(service(db).update_role(role_id, request.name, request.description, request.permission_ids))
    except ValueError as exc: raise error(exc) from exc


@router.delete("/roles/{role_id}", status_code=204)
def delete_role(role_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: service(db).delete_role(role_id)
    except ValueError as exc: raise error(exc) from exc


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    return [permission_response(permission) for permission in service(db).list_permissions()]


@router.post("/permissions", response_model=PermissionResponse, status_code=201)
def create_permission(request: PermissionCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: return permission_response(service(db).create_permission(request.name, request.description))
    except ValueError as exc: raise error(exc) from exc


@router.get("/permissions/{permission_id}", response_model=PermissionResponse)
def get_permission(permission_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    permission = AuthRepository(db).find_permission(permission_id)
    if permission is None: raise HTTPException(status_code=404, detail="Permission not found.")
    return permission_response(permission)


@router.patch("/permissions/{permission_id}", response_model=PermissionResponse)
def update_permission(permission_id: UUID, request: PermissionUpdateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: return permission_response(service(db).update_permission(permission_id, request.name, request.description))
    except ValueError as exc: raise error(exc) from exc


@router.delete("/permissions/{permission_id}", status_code=204)
def delete_permission(permission_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("ACCESS_MANAGE"))):
    try: service(db).delete_permission(permission_id)
    except ValueError as exc: raise error(exc) from exc