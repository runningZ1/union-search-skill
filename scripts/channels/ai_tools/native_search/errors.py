class BackendError(Exception):
    def __init__(self, backend: str, message: str, status: int, retryable: bool):
        super().__init__(message)
        self.backend = backend
        self.status = status
        self.retryable = retryable


def http_failure(backend: str, status: int, message: str) -> BackendError:
    return BackendError(backend, message, status, status == 429 or status >= 500)
