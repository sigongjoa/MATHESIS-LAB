"""
Password Handler for MATHESIS LAB

Handles password hashing, validation, and strength checking.
Uses bcrypt for secure password hashing.
"""

import re
from typing import Tuple

from passlib.context import CryptContext


class PasswordError(Exception):
    """Base exception for password-related errors"""
    pass


class WeakPasswordError(PasswordError):
    """Raised when password does not meet strength requirements"""
    pass


class PasswordHandler:
    """
    Password Handler

    Manages password hashing, verification, and strength validation.
    Uses bcrypt hashing algorithm for security.
    """

    # Password strength requirements
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True

    # Special characters allowed in password
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def __init__(self):
        """Initialize password context with bcrypt"""
        # Using bcrypt with rounds=12 for good security/performance balance
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )

    def hash_password(self, password: str) -> str:
        """
        Hash a plaintext password using bcrypt.

        Args:
            password: Plaintext password to hash

        Returns:
            Hashed password (can be stored in database)

        Example:
            >>> handler = PasswordHandler()
            >>> hashed = handler.hash_password(user_password)
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a hash.

        Args:
            plain_password: Plaintext password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise

        Example:
            >>> handler = PasswordHandler()
            >>> if handler.verify_password(user_input, stored_hash):
            ...     print("Password is correct")
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets strength requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if password meets all requirements
            - error_message: Empty string if valid, otherwise describes the error

        Requirements:
            - Minimum 8 characters
            - At least one uppercase letter (A-Z)
            - At least one lowercase letter (a-z)
            - At least one digit (0-9)
            - At least one special character (!@#$%^&*...)

        Example:
            >>> handler = PasswordHandler()
            >>> is_valid, msg = handler.validate_password_strength("weak")
            >>> if not is_valid:
            ...     print(f"Password error: {msg}")
        """
        # Check minimum length
        if len(password) < self.MIN_LENGTH:
            return False, f"Password must be at least {self.MIN_LENGTH} characters long"

        # Check for uppercase letters
        if self.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter (A-Z)"

        # Check for lowercase letters
        if self.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter (a-z)"

        # Check for digits
        if self.REQUIRE_DIGITS and not re.search(r"\d", password):
            return False, "Password must contain at least one digit (0-9)"

        # Check for special characters
        if self.REQUIRE_SPECIAL_CHARS:
            if not any(char in self.SPECIAL_CHARS for char in password):
                return False, f"Password must contain at least one special character: {self.SPECIAL_CHARS}"

        return True, ""

    def validate_password_strength_strict(self, password: str) -> Tuple[bool, list]:
        """
        Validate password with detailed error reporting.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_list)
            - is_valid: True if password meets all requirements
            - error_list: List of error messages (empty if valid)

        Example:
            >>> handler = PasswordHandler()
            >>> is_valid, errors = handler.validate_password_strength_strict(user_input)
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"- {error}")
        """
        errors = []

        # Check minimum length
        if len(password) < self.MIN_LENGTH:
            errors.append(f"Password must be at least {self.MIN_LENGTH} characters long (current: {len(password)})")

        # Check for uppercase letters
        if self.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Must contain at least one uppercase letter (A-Z)")

        # Check for lowercase letters
        if self.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Must contain at least one lowercase letter (a-z)")

        # Check for digits
        if self.REQUIRE_DIGITS and not re.search(r"\d", password):
            errors.append("Must contain at least one digit (0-9)")

        # Check for special characters
        if self.REQUIRE_SPECIAL_CHARS:
            if not any(char in self.SPECIAL_CHARS for char in password):
                errors.append(f"Must contain at least one special character: {self.SPECIAL_CHARS}")

        return len(errors) == 0, errors

    def get_password_strength_requirements(self) -> dict:
        """
        Get password strength requirements for client-side validation.

        Returns:
            Dictionary with strength requirements

        Example:
            >>> handler = PasswordHandler()
            >>> reqs = handler.get_password_strength_requirements()
            >>> print(f"Min length: {reqs['min_length']}")
        """
        return {
            "min_length": self.MIN_LENGTH,
            "require_uppercase": self.REQUIRE_UPPERCASE,
            "require_lowercase": self.REQUIRE_LOWERCASE,
            "require_digits": self.REQUIRE_DIGITS,
            "require_special_chars": self.REQUIRE_SPECIAL_CHARS,
            "special_chars": self.SPECIAL_CHARS,
            "description": (
                f"Password must be at least {self.MIN_LENGTH} characters long and contain "
                f"uppercase, lowercase, digits, and special characters."
            )
        }


# Singleton instance for application-wide use
_password_handler_instance: PasswordHandler = None


def get_password_handler() -> PasswordHandler:
    """
    Get or create password handler instance.

    Returns:
        PasswordHandler instance
    """
    global _password_handler_instance
    if _password_handler_instance is None:
        _password_handler_instance = PasswordHandler()
    return _password_handler_instance
