"""
보안 유틸리티
Security utilities for password hashing, encryption, and validation
"""

import base64
import hashlib
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config.settings import get_settings
from ..utils.logger import logger

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidator:
    """비밀번호 검증 클래스"""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    # Common weak passwords
    COMMON_PASSWORDS = {
        "password",
        "12345678",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
        "welcome",
        "123456789",
        "password1",
    }

    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"비밀번호는 최소 {cls.MIN_LENGTH}자 이상이어야 합니다")
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"비밀번호는 최대 {cls.MAX_LENGTH}자 이하여야 합니다")

        # Complexity checks
        if not re.search(r"[A-Z]", password):
            errors.append("대문자를 하나 이상 포함해야 합니다")
        if not re.search(r"[a-z]", password):
            errors.append("소문자를 하나 이상 포함해야 합니다")
        if not re.search(r"\d", password):
            errors.append("숫자를 하나 이상 포함해야 합니다")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("특수문자를 하나 이상 포함해야 합니다")

        # Common password check
        if password.lower() in cls.COMMON_PASSWORDS:
            errors.append("일반적으로 사용되는 비밀번호는 사용할 수 없습니다")

        # Sequential character check
        if cls._has_sequential_chars(password):
            errors.append("연속된 문자나 숫자는 사용할 수 없습니다")

        return len(errors) == 0, errors

    @staticmethod
    def _has_sequential_chars(password: str, max_sequential: int = 4) -> bool:
        """Check for sequential characters (4+ consecutive)"""
        for i in range(len(password) - max_sequential + 1):
            substring = password[i : i + max_sequential]

            # Check for sequential numbers
            if substring.isdigit():
                nums = [int(c) for c in substring]
                if all(nums[j] + 1 == nums[j + 1] for j in range(len(nums) - 1)):
                    return True

            # Check for sequential letters
            if substring.isalpha():
                chars = [ord(c.lower()) for c in substring]
                if all(chars[j] + 1 == chars[j + 1] for j in range(len(chars) - 1)):
                    return True

        return False


class PasswordHasher:
    """비밀번호 해싱 클래스"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password"""
        # Use a combination of letters, digits, and special characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

        # Ensure password has at least one of each type
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*"),
        ]

        # Fill the rest randomly
        for _ in range(length - 4):
            password.append(secrets.choice(alphabet))

        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)

        return "".join(password)


class TokenManager:
    """토큰 관리 클래스"""

    def __init__(self):
        settings = get_settings()
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_expiration_hours * 60

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        # Add expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        # Add standard claims
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
            }
        )

        # Create token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token with longer expiration"""
        to_encode = data.copy()

        # Refresh tokens expire in 7 days
        expire = datetime.utcnow() + timedelta(days=7)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": secrets.token_urlsafe(16),
                "type": "refresh",
            }
        )

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"Token decode error: {e}")
            return None

    def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        data = {"email": email, "type": "password_reset"}
        # Password reset tokens expire in 1 hour
        return self.create_access_token(data, expires_delta=timedelta(hours=1))


class DataEncryption:
    """데이터 암호화 클래스"""

    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = key.encode()
        else:
            # Generate key from settings
            settings = get_settings()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=settings.secret_key[:16].encode(),
                iterations=100000,
            )
            self.key = base64.urlsafe_b64encode(
                kdf.derive(settings.secret_key.encode())
            )

        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt dictionary data"""
        import json

        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt dictionary data"""
        import json

        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class InputSanitizer:
    """입력 데이터 살균 클래스"""

    # HTML entities to escape
    HTML_ENTITIES = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }

    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Escape HTML entities"""
        for char, entity in cls.HTML_ENTITIES.items():
            text = text.replace(char, entity)
        return text

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Remove any path components
        filename = filename.replace("..", "")
        filename = filename.replace("/", "")
        filename = filename.replace("\\", "")

        # Keep only safe characters
        safe_chars = string.ascii_letters + string.digits + ".-_"
        sanitized = "".join(c for c in filename if c in safe_chars)

        # Limit length
        return sanitized[:255]

    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """Sanitize SQL identifiers (table/column names)"""
        # Allow only alphanumeric and underscore
        return re.sub(r"[^a-zA-Z0-9_]", "", identifier)

    @staticmethod
    def sanitize_korean_input(text: str) -> str:
        """Sanitize Korean text input"""
        # First remove HTML tags
        text = re.sub(r"<[^>]*>", "", text)

        # Then allow Korean characters, numbers, common punctuation
        pattern = r"[^가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s\.\,\!\?\-\(\)]"
        return re.sub(pattern, "", text)


# Utility functions
def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging"""
    if len(data) <= visible_chars * 2:
        return "*" * len(data)

    start = data[:visible_chars]
    end = data[-visible_chars:]
    masked = "*" * (len(data) - visible_chars * 2)

    return f"{start}{masked}{end}"


def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
    """Check if redirect URL is safe"""
    from urllib.parse import urlparse

    parsed = urlparse(url)

    # Block dangerous protocols
    if parsed.scheme and parsed.scheme.lower() in ["javascript", "data", "vbscript"]:
        return False

    # Relative URLs (no scheme and no netloc) are safe
    if not parsed.netloc and not parsed.scheme:
        return True

    # Check if host is in allowed list
    return parsed.netloc in allowed_hosts
