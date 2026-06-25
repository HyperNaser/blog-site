from exceptions.base import DomainError


class PostDomainError(DomainError):
    """Base exception for all post-related domain errors."""

    pass


class PostNotFoundError(PostDomainError):
    def __init__(self, identifier: str | int):
        super().__init__(f"Post with identifier '{identifier}' could not be found.")


class PermissionDeniedError(PostDomainError):
    def __init__(self, reason: str | None = None):
        msg = "User is not authorized to perform this action."
        if reason:
            msg = f"{msg} {reason}"
        super().__init__(msg)
