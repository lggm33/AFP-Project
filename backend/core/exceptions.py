"""
Custom exceptions for AFP project with structured error handling
"""
from typing import Dict, Any, Optional
from django.utils import timezone
import uuid


class AFPBaseException(Exception):
    """Base exception for all AFP errors with structured metadata"""
    
    error_code: str = "UNKNOWN_ERROR"
    error_category: str = "SYSTEM"
    user_message: str = "An unexpected error occurred"
    log_level: str = "ERROR"
    http_status: int = 500
    retryable: bool = False
    
    def __init__(self, message: str = None, context: Dict[str, Any] = None, user_message: str = None, original_exception: Exception = None):
        self.message = message or self.user_message
        self.context = context or {}
        self.user_message = user_message or self.user_message
        self.original_exception = original_exception
        self.error_id = str(uuid.uuid4())
        self.timestamp = timezone.now()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            'error_id': self.error_id,
            'error_code': self.error_code,
            'error_category': self.error_category,
            'message': self.user_message,
            'timestamp': self.timestamp.isoformat(),
            'retryable': self.retryable
        }
    
    def to_log_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging"""
        return {
            'error_id': self.error_id,
            'error_code': self.error_code,
            'error_category': self.error_category,
            'message': self.message,
            'user_message': self.user_message,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'log_level': self.log_level,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


# =============================================================================
# VALIDATION ERRORS
# =============================================================================

class ValidationError(AFPBaseException):
    """Errors related to data validation"""
    error_code = "VALIDATION_ERROR"
    error_category = "VALIDATION"
    user_message = "Invalid data provided"
    log_level = "WARNING"
    http_status = 400


class RequiredFieldError(ValidationError):
    """Required field is missing"""
    error_code = "REQUIRED_FIELD_ERROR"
    user_message = "Required field is missing"


class InvalidFormatError(ValidationError):
    """Data format is invalid"""
    error_code = "INVALID_FORMAT_ERROR"
    user_message = "Data format is invalid"


# =============================================================================
# AUTHENTICATION & AUTHORIZATION ERRORS
# =============================================================================

class AuthenticationError(AFPBaseException):
    """Authentication related errors"""
    error_code = "AUTH_ERROR"
    error_category = "AUTHENTICATION"
    user_message = "Authentication failed"
    log_level = "WARNING"
    http_status = 401


class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    error_code = "TOKEN_EXPIRED"
    user_message = "Your session has expired. Please log in again."
    retryable = True


class TokenInvalidError(AuthenticationError):
    """Token is invalid"""
    error_code = "TOKEN_INVALID"
    user_message = "Invalid authentication token"


class PermissionDeniedError(AFPBaseException):
    """Permission denied errors"""
    error_code = "PERMISSION_DENIED"
    error_category = "AUTHORIZATION"
    user_message = "You don't have permission to perform this action"
    log_level = "WARNING"
    http_status = 403


# =============================================================================
# EXTERNAL API ERRORS
# =============================================================================

class ExternalAPIError(AFPBaseException):
    """Errors related to external API calls"""
    error_code = "EXTERNAL_API_ERROR"
    error_category = "EXTERNAL"
    user_message = "External service temporarily unavailable"
    log_level = "ERROR"
    http_status = 502
    retryable = True


class GmailAPIError(ExternalAPIError):
    """Gmail API specific errors"""
    error_code = "GMAIL_API_ERROR"
    user_message = "Gmail service temporarily unavailable"


class OAuth2Error(ExternalAPIError):
    """OAuth2 related errors"""
    error_code = "OAUTH2_ERROR"
    user_message = "Authentication with email provider failed"


class RateLimitError(ExternalAPIError):
    """Rate limit exceeded"""
    error_code = "RATE_LIMIT_ERROR"
    user_message = "Too many requests. Please try again later."
    http_status = 429


# =============================================================================
# BUSINESS LOGIC ERRORS
# =============================================================================

class BusinessLogicError(AFPBaseException):
    """Business logic related errors"""
    error_code = "BUSINESS_LOGIC_ERROR"
    error_category = "BUSINESS"
    user_message = "Business rule violation"
    log_level = "WARNING"
    http_status = 400


class IntegrationNotFoundError(BusinessLogicError):
    """Integration not found or not accessible"""
    error_code = "INTEGRATION_NOT_FOUND"
    user_message = "Email integration not found or access denied"
    http_status = 404


class IntegrationInactiveError(BusinessLogicError):
    """Integration is inactive"""
    error_code = "INTEGRATION_INACTIVE"
    user_message = "Email integration is inactive"


class BankSenderNotFoundError(BusinessLogicError):
    """Bank sender not found"""
    error_code = "BANK_SENDER_NOT_FOUND"
    user_message = "Bank sender not found"
    http_status = 404


# =============================================================================
# SYSTEM ERRORS
# =============================================================================

class DatabaseError(AFPBaseException):
    """Database related errors"""
    error_code = "DATABASE_ERROR"
    error_category = "SYSTEM"
    user_message = "Database operation failed"
    log_level = "ERROR"
    http_status = 500


class RedisError(AFPBaseException):
    """Redis related errors"""
    error_code = "REDIS_ERROR"
    error_category = "SYSTEM"
    user_message = "Cache service unavailable"
    log_level = "ERROR"
    http_status = 500
    retryable = True


class CeleryTaskError(AFPBaseException):
    """Celery task errors"""
    error_code = "CELERY_TASK_ERROR"
    error_category = "SYSTEM"
    user_message = "Background task failed"
    log_level = "ERROR"
    http_status = 500
    retryable = True


# =============================================================================
# CONFIGURATION ERRORS
# =============================================================================

class ConfigurationError(AFPBaseException):
    """Configuration related errors"""
    error_code = "CONFIGURATION_ERROR"
    error_category = "CONFIGURATION"
    user_message = "System configuration error"
    log_level = "CRITICAL"
    http_status = 500


class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing"""
    error_code = "MISSING_CONFIGURATION"
    user_message = "System configuration incomplete"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def wrap_exception(func):
    """Decorator to wrap unknown exceptions into AFPBaseException"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AFPBaseException:
            # Re-raise AFP exceptions as-is
            raise
        except Exception as e:
            # Wrap unknown exceptions
            raise AFPBaseException(
                message=f"Unexpected error in {func.__name__}",
                original_exception=e,
                context={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)}
            )
    return wrapper


def categorize_exception(exception: Exception) -> AFPBaseException:
    """Convert standard exceptions to AFP exceptions"""
    if isinstance(exception, AFPBaseException):
        return exception
    
    # Map common Django/Python exceptions
    exception_mapping = {
        'ValidationError': ValidationError,
        'PermissionDenied': PermissionDeniedError,
        'Http404': BusinessLogicError,
        'IntegrityError': DatabaseError,
        'OperationalError': DatabaseError,
        'ConnectionError': ExternalAPIError,
        'Timeout': ExternalAPIError,
    }
    
    exception_type = type(exception).__name__
    afp_exception_class = exception_mapping.get(exception_type, AFPBaseException)
    
    return afp_exception_class(
        message=str(exception),
        original_exception=exception
    ) 