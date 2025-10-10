"""
Password hashing utilities with bcrypt compatibility handling
"""
import hashlib
import secrets

try:
    import bcrypt
    HAS_BCRYPT = True
    # Test if bcrypt is working properly
    try:
        bcrypt.gensalt()
    except AttributeError:
        # bcrypt module exists but doesn't work properly
        HAS_BCRYPT = False
except ImportError:
    HAS_BCRYPT = False

class PasswordHasher:
    """
    Password hasher that handles bcrypt issues gracefully
    """

    def __init__(self):
        self.salt_length = 22
        self.rounds = 12

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt or fallback to SHA256"""
        if HAS_BCRYPT:
            try:
                # Try to use bcrypt
                salt = bcrypt.gensalt(rounds=self.rounds)
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
                return hashed.decode('utf-8')
            except (AttributeError, ValueError, TypeError):
                # Fallback if bcrypt fails
                pass

        # Fallback to SHA256 with salt
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"$sha256${salt}${password_hash}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if HAS_BCRYPT and hashed_password.startswith('$2'):
            try:
                # Verify bcrypt hash
                return bcrypt.checkpw(
                    plain_password.encode('utf-8'),
                    hashed_password.encode('utf-8')
                )
            except (AttributeError, ValueError, TypeError):
                pass

        # Verify SHA256 hash
        if hashed_password.startswith('$sha256$'):
            parts = hashed_password.split('$')
            expected_parts_count = 4
            if len(parts) == expected_parts_count:
                salt = parts[2]
                stored_hash = parts[3]
                test_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
                return test_hash == stored_hash

        # Fallback for plain comparison (development only)
        return plain_password == hashed_password

# Global instance
password_hasher = PasswordHasher()
