class AuthenticationError(Exception):
    """Base authentication error."""


class MissingTokenError(AuthenticationError):
    """Raised when an access token is missing."""


class InvalidTokenError(AuthenticationError):
    """Raised when an access token is invalid."""


class ExpiredTokenError(AuthenticationError):
    """Raised when an access token has expired."""


class UnauthorizedError(AuthenticationError):
    """Raised when authentication is required or rejected."""


class ForbiddenError(AuthenticationError):
    """Raised when an authenticated user lacks permission."""
