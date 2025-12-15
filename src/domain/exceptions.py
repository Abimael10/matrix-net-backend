class DomainError(Exception):
    """Base class for domain-level exceptions."""


class UserExists(DomainError):
    pass


class PostNotFound(DomainError):
    pass


class Unauthorized(DomainError):
    pass


class InvalidOperation(DomainError):
    pass
