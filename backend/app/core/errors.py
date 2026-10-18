class DomainError(Exception):
    """An expected failure that services raise instead of HTTPException.

    Services stay free of HTTP so background workers can reuse them; the HTTP layer
    turns these into responses (see error_handlers.py). Subclasses set status_code.
    """

    status_code = 400

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
