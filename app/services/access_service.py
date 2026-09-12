from uuid import UUID

from app.models.auth import Permission, Role, User
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import hash_password, normalize_email


class AccessService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    def _roles(self, role_ids: list[UUID]) -> list[Role]:
        roles = [role for role_id in role_ids if (role := self.repository.find_role(role_id)) is not None]
        if len(roles) != len(set(role_ids)):
            raise ValueError("One or more roles do not exist.")
        return roles

    def _permissions(self, permission_ids: list[UUID]) -> list[Permission]:
        permissions = [permission for permission_id in permission_ids if (permission := self.repository.find_permission(permission_id)) is not None]
        if len(permissions) != len(set(permission_ids)):
            raise ValueError("One or more permissions do not exist.")
        return permissions

    def list_users(self): return self.repository.list_users()
    def list_roles(self): return self.repository.list_roles()
    def list_permissions(self): return self.repository.list_permissions()

    def create_user(self, email: str, full_name: str, password: str, role_ids: list[UUID]) -> User:
        email = normalize_email(email)
        if self.repository.find_user_by_email(email): raise ValueError("A user with that email already exists.")
        user = User(email=email, full_name=full_name.strip(), password_hash=hash_password(password), roles=self._roles(role_ids))
        self.repository.save(user); self.repository.commit(); return user

    def update_user(self, actor: User, user_id: UUID, email: str | None, full_name: str | None, role_ids: list[UUID] | None, is_active: bool | None) -> User:
        user = self.repository.find_user(user_id)
        if user is None: raise ValueError("User not found.")
        if is_active is False and user.id == actor.id: raise ValueError("You cannot deactivate your own account.")
        if is_active is False and user.is_active and any(role.name == "ADMIN" for role in user.roles) and self.repository.count_active_admins() <= 1:
            raise ValueError("Cannot deactivate the last active ADMIN.")
        if email is not None:
            normalized = normalize_email(email)
            existing = self.repository.find_user_by_email(normalized)
            if existing is not None and existing.id != user.id: raise ValueError("A user with that email already exists.")
            user.email = normalized
        if full_name is not None: user.full_name = full_name.strip()
        if role_ids is not None:
            next_roles = self._roles(role_ids)
            removing_admin = user.is_active and any(role.name == "ADMIN" for role in user.roles) and not any(role.name == "ADMIN" for role in next_roles)
            if removing_admin and self.repository.count_active_admins() <= 1:
                raise ValueError("Cannot remove ADMIN from the last active ADMIN user.")
            user.roles = next_roles
        if is_active is not None: user.is_active = is_active
        self.repository.commit(); return user

    def reset_password(self, user_id: UUID, password: str) -> None:
        user = self.repository.find_user(user_id)
        if user is None: raise ValueError("User not found.")
        user.password_hash = hash_password(password); self.repository.commit()

    def delete_user(self, actor: User, user_id: UUID) -> None:
        self.update_user(actor, user_id, None, None, None, False)

    def create_role(self, name: str, description: str | None, permission_ids: list[UUID]) -> Role:
        normalized = name.strip().upper()
        if any(role.name == normalized for role in self.repository.list_roles()): raise ValueError("A role with that name already exists.")
        role = Role(name=normalized, description=description, permissions=self._permissions(permission_ids))
        self.repository.save(role); self.repository.commit(); return role

    def update_role(self, role_id: UUID, name: str | None, description: str | None, permission_ids: list[UUID] | None) -> Role:
        role = self.repository.find_role(role_id)
        if role is None: raise ValueError("Role not found.")
        if name is not None:
            normalized = name.strip().upper()
            if any(existing.id != role.id and existing.name == normalized for existing in self.repository.list_roles()):
                raise ValueError("A role with that name already exists.")
            role.name = normalized
        if description is not None: role.description = description
        if permission_ids is not None: role.permissions = self._permissions(permission_ids)
        self.repository.commit(); return role

    def delete_role(self, role_id: UUID) -> None:
        role = self.repository.find_role(role_id)
        if role is None: raise ValueError("Role not found.")
        if role.name == "ADMIN" or self.repository.count_role_users(role_id): raise ValueError("Assigned or protected roles cannot be deleted.")
        self.repository.delete(role); self.repository.commit()

    def create_permission(self, name: str, description: str | None) -> Permission:
        normalized = name.strip().upper()
        if any(permission.name == normalized for permission in self.repository.list_permissions()): raise ValueError("A permission with that name already exists.")
        permission = Permission(name=normalized, description=description)
        self.repository.save(permission); self.repository.commit(); return permission

    def update_permission(self, permission_id: UUID, name: str | None, description: str | None) -> Permission:
        permission = self.repository.find_permission(permission_id)
        if permission is None: raise ValueError("Permission not found.")
        if name is not None:
            normalized = name.strip().upper()
            if any(existing.id != permission.id and existing.name == normalized for existing in self.repository.list_permissions()):
                raise ValueError("A permission with that name already exists.")
            permission.name = normalized
        if description is not None: permission.description = description
        self.repository.commit(); return permission

    def delete_permission(self, permission_id: UUID) -> None:
        permission = self.repository.find_permission(permission_id)
        if permission is None: raise ValueError("Permission not found.")
        if self.repository.count_permission_roles(permission_id): raise ValueError("Permission is assigned to a role and cannot be deleted.")
        self.repository.delete(permission); self.repository.commit()