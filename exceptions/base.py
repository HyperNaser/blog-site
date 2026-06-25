from fastapi import status


class DomainError(Exception):
    """Base exception for all system-wide business logic violations."""

    http_status = status.HTTP_400_BAD_REQUEST

    pass
