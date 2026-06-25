from fastapi import status

from exceptions.base import DomainError


class PostDomainError(DomainError):
    """Base exception for all post-related domain errors."""

    pass


class PostNotFoundError(PostDomainError):
    http_status = status.HTTP_404_NOT_FOUND

    def __init__(self, identifier: str | int):
        super().__init__(f"Post with identifier '{identifier}' could not be found.")


class PermissionDeniedError(PostDomainError):
    http_status = status.HTTP_403_FORBIDDEN

    def __init__(self, reason: str | None = None):
        msg = "User is not authorized to perform this action."
        if reason:
            msg = f"{msg} {reason}"
        super().__init__(msg)
