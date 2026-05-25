import bcrypt

# tell passlib to handle bcrypt hashing


def hash_password(password: str) -> str:
    """Generate a secure , salted bcrypt hash string from plain text password."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies an incoming login password against the database record hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
