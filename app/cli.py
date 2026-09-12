import getpass
import sys

from app.db.database import SessionLocal
from app.models.auth import User
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import hash_password, normalize_email


def create_admin() -> None:
    email = normalize_email(input("Email: "))
    full_name = input("Full name: ").strip()
    password = getpass.getpass("Password: ")
    repository = AuthRepository(SessionLocal())
    try:
        if repository.find_user_by_email(email) is not None:
            print("A user with that email already exists.")
            return
        role = repository.find_role_by_name("ADMIN")
        if role is None:
            raise RuntimeError("ADMIN role is missing. Run alembic upgrade head first.")
        user = User(email=email, full_name=full_name, password_hash=hash_password(password), roles=[role])
        repository.save(user)
        repository.commit()
        print(f"Created ADMIN user {email}.")
    finally:
        repository.db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "create-admin":
        raise SystemExit("Usage: python -m app.cli create-admin")
    create_admin()