#!/usr/bin/env python3
"""Shared CLI error types."""

from typing import Optional


class CliError(Exception):
    """Base CLI error with exit code."""

    def __init__(self, message: str, exit_code: int = 1, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.detail = detail


class CliUsageError(CliError):
    """User input / argument error."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message=message, exit_code=1, detail=detail)


class CliRuntimeError(CliError):
    """Runtime / platform execution error."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message=message, exit_code=2, detail=detail)
