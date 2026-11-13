import hashlib
import secrets
from typing import Optional, Dict, Any, Tuple
from src.database.db import DatabaseManager


def hash_password(password: str, salt: str) -> str:
    """Hash password using PBKDF2 HMAC SHA-256 with 100,000 iterations."""
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return key.hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify password in constant time to prevent timing attacks."""
    computed_hash = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, password_hash)


def authenticate(username: str, password: str, db: DatabaseManager) -> Optional[Dict[str, Any]]:
    """Authenticate credentials against database."""
    clean_username = username.strip().lower()
    user = db.get_user(clean_username)
    if not user:
        return None
    
    if verify_password(password, user["salt"], user["password_hash"]):
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
    return None


def register_user(
    username: str,
    password: str,
    role: str = "user",
    db: Optional[DatabaseManager] = None,
) -> Tuple[bool, str]:
    """Register a new user account with role."""
    if not db:
        from src.database.db import get_db
        db = get_db()

    clean_username = username.strip().lower()
    if len(clean_username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(password) < 4:
        return False, "Password must be at least 4 characters long."
    if role not in ["admin", "user"]:
        return False, "Invalid role specified."

    existing = db.get_user(clean_username)
    if existing:
        return False, f"Username '{clean_username}' is already taken."

    salt = secrets.token_hex(16)
    pwd_hash = hash_password(password, salt)
    db.create_user(
        username=clean_username,
        password_hash=pwd_hash,
        salt=salt,
        role=role,
    )
    return True, f"Account '{clean_username}' registered successfully as {role}."


def ensure_default_accounts(db: DatabaseManager):
    """Seed default Admin and Demo User accounts if not present."""
    # 1. Default Admin
    if not db.get_user("admin"):
        salt = secrets.token_hex(16)
        pwd_hash = hash_password("admin123", salt)
        db.create_user(username="admin", password_hash=pwd_hash, salt=salt, role="admin")

    # 2. Default User
    if not db.get_user("user"):
        salt = secrets.token_hex(16)
        pwd_hash = hash_password("user123", salt)
        db.create_user(username="user", password_hash=pwd_hash, salt=salt, role="user")
