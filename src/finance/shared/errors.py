class FinanceError(Exception):
    """Expected domain error safe to expose to clients."""

    code = "FINANCE_ERROR"
    status_code = 400

    def __init__(self, message: str, *, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(FinanceError):
    code = "NOT_FOUND"
    status_code = 404


class ConflictError(FinanceError):
    code = "CONFLICT"
    status_code = 409


class AuthorizationError(FinanceError):
    code = "FORBIDDEN"
    status_code = 403
