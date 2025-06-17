"""
Structured logging system for AFP project
Can be easily migrated to Sentry/DataDog later
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from collections import defaultdict
import threading

from core.exceptions import AFPBaseException


class StructuredLogger:
    """
    Structured logger that creates JSON formatted logs with context
    Easy to migrate to external services like Sentry/DataDog
    """
    
    def __init__(self, name: str = None):
        self.name = name or __name__
        self.logger = logging.getLogger(self.name)
        self._local = threading.local()
        
    def _get_base_context(self, user: User = None, request_id: str = None) -> Dict[str, Any]:
        """Get base context for all log entries"""
        context = {
            'timestamp': timezone.now().isoformat(),
            'service': 'afp-backend',
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
            'version': getattr(settings, 'VERSION', '1.0.0'),
        }
        
        if user:
            context['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            
        if request_id:
            context['request_id'] = request_id
            
        # Add request context if available
        if hasattr(self._local, 'request_context'):
            context.update(self._local.request_context)
            
        return context
    
    def set_request_context(self, request_id: str = None, ip: str = None, 
                          user_agent: str = None, endpoint: str = None):
        """Set request context for current thread"""
        self._local.request_context = {
            'request_id': request_id,
            'client_ip': ip,
            'user_agent': user_agent,
            'endpoint': endpoint
        }
    
    def clear_request_context(self):
        """Clear request context for current thread"""
        if hasattr(self._local, 'request_context'):
            delattr(self._local, 'request_context')
    
    def _log(self, level: str, message: str, extra_context: Dict[str, Any] = None,
             user: User = None, request_id: str = None, exception: Exception = None):
        """Internal logging method"""
        
        # Build log entry
        log_entry = self._get_base_context(user, request_id)
        log_entry.update({
            'level': level,
            'message': message,
            'context': extra_context or {}
        })
        
        # Add exception details if provided
        if exception:
            if isinstance(exception, AFPBaseException):
                log_entry['error'] = exception.to_log_dict()
            else:
                log_entry['error'] = {
                    'type': type(exception).__name__,
                    'message': str(exception),
                    'traceback': self._get_traceback() if level in ['ERROR', 'CRITICAL'] else None
                }
        
        # Log as JSON
        log_message = json.dumps(log_entry, default=str, ensure_ascii=False)
        
        # Send to appropriate log level
        if level == 'DEBUG':
            self.logger.debug(log_message)
        elif level == 'INFO':
            self.logger.info(log_message)
        elif level == 'WARNING':
            self.logger.warning(log_message)
        elif level == 'ERROR':
            self.logger.error(log_message)
        elif level == 'CRITICAL':
            self.logger.critical(log_message)
    
    def _get_traceback(self) -> str:
        """Get current traceback as string"""
        import traceback
        return traceback.format_exc()
    
    # Public logging methods
    def debug(self, message: str, extra_context: Dict[str, Any] = None,
              user: User = None, request_id: str = None):
        self._log('DEBUG', message, extra_context, user, request_id)
    
    def info(self, message: str, extra_context: Dict[str, Any] = None,
             user: User = None, request_id: str = None):
        self._log('INFO', message, extra_context, user, request_id)
    
    def warning(self, message: str, extra_context: Dict[str, Any] = None,
                user: User = None, request_id: str = None, exception: Exception = None):
        self._log('WARNING', message, extra_context, user, request_id, exception)
    
    def error(self, message: str, extra_context: Dict[str, Any] = None,
              user: User = None, request_id: str = None, exception: Exception = None):
        self._log('ERROR', message, extra_context, user, request_id, exception)
    
    def critical(self, message: str, extra_context: Dict[str, Any] = None,
                 user: User = None, request_id: str = None, exception: Exception = None):
        self._log('CRITICAL', message, extra_context, user, request_id, exception)
    
    # Specialized logging methods
    def log_api_request(self, method: str, endpoint: str, user: User = None, 
                       request_id: str = None, duration_ms: float = None,
                       status_code: int = None, payload_size: int = None):
        """Log API request with performance metrics"""
        context = {
            'api_request': {
                'method': method,
                'endpoint': endpoint,
                'duration_ms': duration_ms,
                'status_code': status_code,
                'payload_size': payload_size
            }
        }
        self.info(f"API Request: {method} {endpoint}", context, user, request_id)
    
    def log_external_api_call(self, service: str, endpoint: str, method: str,
                             duration_ms: float = None, status_code: int = None,
                             user: User = None, request_id: str = None):
        """Log external API calls"""
        context = {
            'external_api': {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'duration_ms': duration_ms,
                'status_code': status_code
            }
        }
        self.info(f"External API Call: {service}", context, user, request_id)
    
    def log_business_event(self, event: str, entity: str, entity_id: Union[str, int],
                          user: User = None, request_id: str = None, 
                          extra_data: Dict[str, Any] = None):
        """Log business events"""
        context = {
            'business_event': {
                'event': event,
                'entity': entity,
                'entity_id': str(entity_id),
                'extra_data': extra_data or {}
            }
        }
        self.info(f"Business Event: {event}", context, user, request_id)
    
    def log_security_event(self, event: str, user: User = None, request_id: str = None,
                          ip_address: str = None, user_agent: str = None,
                          severity: str = 'WARNING'):
        """Log security events"""
        context = {
            'security_event': {
                'event': event,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'severity': severity
            }
        }
        if severity == 'CRITICAL':
            self.critical(f"Security Event: {event}", context, user, request_id)
        else:
            self.warning(f"Security Event: {event}", context, user, request_id)


class ErrorTracker:
    """
    Simple error tracking system that can be easily migrated to Sentry
    """
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_rates = defaultdict(list)
        self.logger = StructuredLogger('error_tracker')
    
    def track_error(self, exception: AFPBaseException, user: User = None, 
                   request_id: str = None):
        """Track error occurrence"""
        error_code = exception.error_code
        error_category = exception.error_category
        
        # Increment counter
        self.error_counts[error_code] += 1
        
        # Track rate (errors per hour)
        current_hour = datetime.now().hour
        self.error_rates[error_code].append(current_hour)
        
        # Log the error
        self.logger.error(
            f"Error tracked: {error_code}",
            extra_context={
                'error_tracking': {
                    'error_code': error_code,
                    'error_category': error_category,
                    'total_count': self.error_counts[error_code],
                    'recent_occurrences': len([h for h in self.error_rates[error_code] 
                                             if h == current_hour])
                }
            },
            user=user,
            request_id=request_id,
            exception=exception
        )
        
        # Check if we should alert
        if self.should_alert(error_code):
            self.send_alert(exception, user, request_id)
    
    def should_alert(self, error_code: str) -> bool:
        """Determine if we should send an alert for this error"""
        current_hour = datetime.now().hour
        recent_errors = len([h for h in self.error_rates[error_code] 
                           if h == current_hour])
        
        # Alert thresholds
        alert_thresholds = {
            'CRITICAL': 1,    # Alert on first critical error
            'ERROR': 5,       # Alert after 5 errors per hour
            'WARNING': 20     # Alert after 20 warnings per hour
        }
        
        # Get error level from first occurrence
        # This is simplified - in production you'd store this properly
        return recent_errors >= alert_thresholds.get('ERROR', 5)
    
    def send_alert(self, exception: AFPBaseException, user: User = None, 
                  request_id: str = None):
        """Send alert (placeholder for future Sentry/email integration)"""
        alert_data = {
            'alert_type': 'error_threshold_exceeded',
            'error_code': exception.error_code,
            'error_category': exception.error_category,
            'user_id': user.id if user else None,
            'request_id': request_id,
            'timestamp': timezone.now().isoformat()
        }
        
        # For now, just log as critical
        self.logger.critical(
            f"ALERT: Error threshold exceeded for {exception.error_code}",
            extra_context={'alert': alert_data},
            user=user,
            request_id=request_id
        )
        
        # TODO: Integrate with Sentry, email alerts, Slack, etc.
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics"""
        return {
            'total_errors': dict(self.error_counts),
            'error_rates': {k: len(v) for k, v in self.error_rates.items()},
            'top_errors': sorted(self.error_counts.items(), 
                               key=lambda x: x[1], reverse=True)[:10]
        }


# Global instances
structured_logger = StructuredLogger('afp')
error_tracker = ErrorTracker()

# Convenience functions
def log_info(message: str, **kwargs):
    structured_logger.info(message, **kwargs)

def log_error(message: str, **kwargs):
    structured_logger.error(message, **kwargs)

def log_warning(message: str, **kwargs):
    structured_logger.warning(message, **kwargs)

def track_error(exception: AFPBaseException, **kwargs):
    error_tracker.track_error(exception, **kwargs) 