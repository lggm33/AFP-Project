"""
Error handling middleware for AFP project
Provides consistent error responses and logging
"""
import json
import uuid
from typing import Dict, Any
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.exceptions import AFPBaseException, categorize_exception
from core.logging.structured_logger import structured_logger, error_tracker


class ErrorHandlerMiddleware(MiddlewareMixin):
    """
    Middleware to handle exceptions and provide consistent error responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> None:
        """Set request context for logging"""
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Set request context in logger
        structured_logger.set_request_context(
            request_id=request_id,
            ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            endpoint=f"{request.method} {request.path}"
        )
        
        # Log request
        structured_logger.log_api_request(
            method=request.method,
            endpoint=request.path,
            user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
            request_id=request_id
        )
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response and clean up context"""
        if hasattr(request, 'request_id'):
            # Log response
            structured_logger.log_api_request(
                method=request.method,
                endpoint=request.path,
                user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                request_id=request.request_id,
                status_code=response.status_code,
                payload_size=len(response.content) if hasattr(response, 'content') else 0
            )
        
        # Clear request context
        structured_logger.clear_request_context()
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> JsonResponse:
        """Handle exceptions and return consistent error responses"""
        
        # Convert to AFP exception if needed
        if not isinstance(exception, AFPBaseException):
            afp_exception = categorize_exception(exception)
        else:
            afp_exception = exception
        
        # Get request context
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Track error
        error_tracker.track_error(afp_exception, user=user, request_id=request_id)
        
        # Log error with context
        structured_logger.error(
            f"Unhandled exception: {afp_exception.error_code}",
            extra_context={
                'endpoint': f"{request.method} {request.path}",
                'client_ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'request_data': self.get_safe_request_data(request)
            },
            user=user,
            request_id=request_id,
            exception=afp_exception
        )
        
        # Build error response
        error_response = self.build_error_response(afp_exception, request_id)
        
        # Clean up context
        structured_logger.clear_request_context()
        
        return JsonResponse(
            error_response,
            status=afp_exception.http_status,
            json_dumps_params={'ensure_ascii': False}
        )
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_safe_request_data(self, request: HttpRequest) -> Dict[str, Any]:
        """Get request data safely (excluding sensitive information)"""
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                if hasattr(request, 'data'):
                    # DRF request
                    data = dict(request.data)
                else:
                    # Django request
                    data = dict(request.POST)
                
                # Remove sensitive fields
                sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
                for field in sensitive_fields:
                    for key in list(data.keys()):
                        if any(sensitive in key.lower() for sensitive in sensitive_fields):
                            data[key] = '[REDACTED]'
                
                return data
            else:
                return dict(request.GET)
        except Exception:
            return {'error': 'Could not parse request data'}
    
    def build_error_response(self, exception: AFPBaseException, request_id: str) -> Dict[str, Any]:
        """Build consistent error response"""
        error_response = exception.to_dict()
        error_response['request_id'] = request_id
        
        # Add debug info in development
        if settings.DEBUG:
            error_response['debug'] = {
                'internal_message': exception.message,
                'context': exception.context,
                'original_exception': str(exception.original_exception) if exception.original_exception else None
            }
        
        return {
            'success': False,
            'error': error_response
        }


def custom_drf_exception_handler(exc, context):
    """
    Custom DRF exception handler that integrates with our error system
    """
    # Get the standard DRF response first
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # Convert DRF exceptions to AFP exceptions
        request = context.get('request')
        view = context.get('view')
        
        # Get request context
        request_id = getattr(request, 'request_id', str(uuid.uuid4())) if request else str(uuid.uuid4())
        user = getattr(request, 'user', None) if request and hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Convert to AFP exception
        if not isinstance(exc, AFPBaseException):
            afp_exception = categorize_exception(exc)
        else:
            afp_exception = exc
        
        # Track error
        error_tracker.track_error(afp_exception, user=user, request_id=request_id)
        
        # Log error
        structured_logger.error(
            f"DRF exception: {afp_exception.error_code}",
            extra_context={
                'view': str(view) if view else None,
                'endpoint': f"{request.method} {request.path}" if request else None,
                'drf_response': response.data if hasattr(response, 'data') else None
            },
            user=user,
            request_id=request_id,
            exception=afp_exception
        )
        
        # Build custom response
        error_response = afp_exception.to_dict()
        error_response['request_id'] = request_id
        
        # Add debug info in development
        if settings.DEBUG:
            error_response['debug'] = {
                'internal_message': afp_exception.message,
                'context': afp_exception.context,
                'original_drf_response': response.data if hasattr(response, 'data') else None
            }
        
        # Update response data
        response.data = {
            'success': False,
            'error': error_response
        }
    
    return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log request/response details for monitoring
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Log incoming request"""
        request.start_time = timezone.now()
        
        # Skip logging for certain paths
        skip_paths = ['/health/', '/metrics/', '/admin/']
        if any(request.path.startswith(path) for path in skip_paths):
            return
        
        user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        structured_logger.info(
            f"Request started: {request.method} {request.path}",
            extra_context={
                'request_start': {
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'content_type': request.content_type,
                    'content_length': request.META.get('CONTENT_LENGTH', 0)
                }
            },
            user=user,
            request_id=request_id
        )
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response details"""
        # Skip logging for certain paths
        skip_paths = ['/health/', '/metrics/', '/admin/']
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        # Calculate duration
        duration_ms = None
        if hasattr(request, 'start_time'):
            duration = timezone.now() - request.start_time
            duration_ms = duration.total_seconds() * 1000
        
        user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = 'ERROR'
        elif response.status_code >= 400:
            log_level = 'WARNING'
        else:
            log_level = 'INFO'
        
        message = f"Request completed: {request.method} {request.path} - {response.status_code}"
        
        context = {
            'request_complete': {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'response_size': len(response.content) if hasattr(response, 'content') else 0
            }
        }
        
        if log_level == 'ERROR':
            structured_logger.error(message, extra_context=context, user=user, request_id=request_id)
        elif log_level == 'WARNING':
            structured_logger.warning(message, extra_context=context, user=user, request_id=request_id)
        else:
            structured_logger.info(message, extra_context=context, user=user, request_id=request_id)
        
        return response 