from exceptions.base import DomainError


class AuthDomainError(DomainError):
    """Base exception for all auth-related domain errors."""

    pass


class IncorrectCredentialsError(AuthDomainError):
    def __init__(self, reason: str = "Incorrect username or password.") -> None:
        super().__init__(reason)


class InvalidTokenError(AuthDomainError):
    def __init__(self, detail: str = "Could not validate credentials.") -> None:
        super().__init__(detail)
