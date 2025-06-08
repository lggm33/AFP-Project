"""
Security Audit System for OAuth Token Management
Monitors and logs all token-related activities
"""

import logging
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import models
from allauth.socialaccount.models import SocialToken
from django.utils import timezone

logger = logging.getLogger('security.oauth')

class TokenAccessLog(models.Model):
    """Log all OAuth token access for security auditing"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)  # google, microsoft, yahoo
    action = models.CharField(max_length=50)    # access, refresh, revoke
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'oauth_token_access_log'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['provider', 'timestamp']),
        ]

class SecurityAuditor:
    """Centralized security auditing for OAuth operations"""
    
    @staticmethod
    def log_token_access(user: User, provider: str, action: str, 
                        request=None, success=True, error_message=''):
        """Log token access with context information"""
        
        ip_address = None
        user_agent = ''
        
        if request:
            ip_address = SecurityAuditor.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        TokenAccessLog.objects.create(
            user=user,
            provider=provider,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message[:1000] if error_message else ''
        )
        
        # Also log to Django logger for immediate monitoring
        log_level = logging.INFO if success else logging.ERROR
        logger.log(log_level, 
            f"OAuth {action}: user={user.username}, provider={provider}, "
            f"ip={ip_address}, success={success}, error={error_message}"
        )
    
    @staticmethod
    def get_client_ip(request):
        """Extract real client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def detect_suspicious_activity(user: User, provider: str) -> dict:
        """Detect potentially suspicious OAuth activity"""
        
        suspicious_indicators = {
            'multiple_ips_recent': False,
            'excessive_requests': False,
            'unusual_hours': False,
            'failed_attempts': False
        }
        
        # Check last 24 hours of activity
        last_24h = timezone.now() - timedelta(hours=24)
        recent_logs = TokenAccessLog.objects.filter(
            user=user,
            provider=provider,
            timestamp__gte=last_24h
        )
        
        # Multiple IPs in short time
        unique_ips = recent_logs.values_list('ip_address', flat=True).distinct()
        if len(unique_ips) > 3:
            suspicious_indicators['multiple_ips_recent'] = True
        
        # Excessive requests
        if recent_logs.count() > 100:
            suspicious_indicators['excessive_requests'] = True
        
        # Failed attempts
        failed_count = recent_logs.filter(success=False).count()
        if failed_count > 5:
            suspicious_indicators['failed_attempts'] = True
        
        # Activity during unusual hours (2AM - 6AM local time)
        night_activity = recent_logs.filter(
            timestamp__hour__in=[2, 3, 4, 5, 6]
        ).count()
        if night_activity > 10:
            suspicious_indicators['unusual_hours'] = True
        
        return suspicious_indicators
    
    @staticmethod
    def generate_security_report(days: int = 7) -> dict:
        """Generate security report for OAuth usage"""
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        total_accesses = TokenAccessLog.objects.filter(
            timestamp__gte=cutoff_date
        ).count()
        
        failed_accesses = TokenAccessLog.objects.filter(
            timestamp__gte=cutoff_date,
            success=False
        ).count()
        
        unique_users = TokenAccessLog.objects.filter(
            timestamp__gte=cutoff_date
        ).values_list('user_id', flat=True).distinct().count()
        
        providers_usage = TokenAccessLog.objects.filter(
            timestamp__gte=cutoff_date
        ).values('provider').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        return {
            'period_days': days,
            'total_token_accesses': total_accesses,
            'failed_accesses': failed_accesses,
            'success_rate': (total_accesses - failed_accesses) / total_accesses * 100 if total_accesses > 0 else 0,
            'unique_users': unique_users,
            'providers_usage': list(providers_usage),
            'generated_at': timezone.now().isoformat()
        }

# Security middleware hooks
def audit_token_usage(func):
    """Decorator to audit OAuth token usage"""
    def wrapper(self, *args, **kwargs):
        user = getattr(self, 'user', None)
        provider = getattr(self, 'provider', 'unknown')
        
        try:
            result = func(self, *args, **kwargs)
            if user:
                SecurityAuditor.log_token_access(
                    user=user,
                    provider=provider,
                    action=func.__name__,
                    success=True
                )
            return result
        except Exception as e:
            if user:
                SecurityAuditor.log_token_access(
                    user=user,
                    provider=provider,
                    action=func.__name__,
                    success=False,
                    error_message=str(e)
                )
            raise
    
    return wrapper 