"""
Custom Exceptions
=================

This module defines custom exceptions for the application.

IMPROVEMENT OPPORTUNITIES:
1. Add error codes for easier debugging
2. Add error context/traceback information
3. Implement error logging
4. Add error recovery strategies
"""


class AMZEagleException(Exception):
    """Base exception for all application errors."""

    pass


class KeepaAPIError(AMZEagleException):
    """Exception raised for Keepa API errors."""

    pass


class DataProcessingError(AMZEagleException):
    """Exception raised for data processing errors."""

    pass


class ScoringError(AMZEagleException):
    """Exception raised for scoring engine errors."""

    pass


class ForecastingError(AMZEagleException):
    """Exception raised for forecasting errors."""

    pass


class EconomicsError(AMZEagleException):
    """Exception raised for economics calculation errors."""

    pass


class ValidationError(AMZEagleException):
    """Exception raised for validation errors."""

    pass


class ConfigurationError(AMZEagleException):
    """Exception raised for configuration errors."""

    pass


class DatabaseError(AMZEagleException):
    """Exception raised for database errors."""

    pass
