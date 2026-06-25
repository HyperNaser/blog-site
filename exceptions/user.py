from fastapi import status

from exceptions.base import DomainError


class UserDomainError(DomainError):
    """Base exception for all user-related domain errors."""

    pass


class UsernameTakenError(UserDomainError):
    def __init__(self, username: str):
        super().__init__(f"The username '{username}' is already taken.")


class EmailTakenError(UserDomainError):
    def __init__(self, email: str):
        super().__init__(f"The email '{email}' is already registered.")


class UserNotFoundError(UserDomainError):
    http_status = status.HTTP_404_NOT_FOUND

    def __init__(self, identifier: str | int):
        super().__init__(f"User with identifier '{identifier}' could not be found.")


class InvalidImageError(UserDomainError):
    def __init__(self) -> None:
        super().__init__("Invalid image file. Please upload a valid image.")


class ImageSizeTooLargeError(UserDomainError):
    def __init__(self, max_mb: int) -> None:
        super().__init__(f"File too large. Maximum size is {max_mb}MB")


class ImageNotFoundError(UserDomainError):
    def __init__(self, detail: str | None = "Image not found.") -> None:
        super().__init__(detail)
