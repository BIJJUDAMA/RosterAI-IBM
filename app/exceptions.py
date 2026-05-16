class AppError(Exception):
    """Base exception for all application-specific errors."""
    def __init__(self, message: str, detail: str = None):
        super().__init__(message)
        self.message = message
        self.detail = detail

class LLMError(AppError):
    """Raised when there is an issue with the LLM service."""
    pass

class LLMTimeoutError(LLMError):
    """Raised when the LLM request times out."""
    pass

class LLMConnectionError(LLMError):
    """Raised when the LLM service is unreachable."""
    pass

class LLMParseError(LLMError):
    """Raised when the LLM response is not in the expected format (e.g., invalid JSON)."""
    pass

class ExtractionError(AppError):
    """Raised when document extraction (text or image) fails."""
    pass

class DatabaseError(AppError):
    """Raised when a database operation fails."""
    pass

class IngestionError(AppError):
    """Raised when a specific file fails during ingestion."""
    def __init__(self, filename: str, message: str, detail: str = None):
        full_msg = f"Failed to ingest {filename}: {message}"
        super().__init__(full_msg, detail)
        self.filename = filename
