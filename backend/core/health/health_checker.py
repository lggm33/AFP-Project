"""
Health check system for AFP project
Monitors system components and dependencies
"""
import time
import redis
from typing import Dict, Any, List
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests

from core.logging.structured_logger import structured_logger
from core.exceptions import DatabaseError, RedisError, ExternalAPIError


class HealthChecker:
    """
    System health checker that monitors all critical components
    """
    
    def __init__(self):
        self.logger = structured_logger
    
    def check_all_systems(self) -> Dict[str, Any]:
        """Check all system components and return health status"""
        start_time = time.time()
        
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
        
        # Define all health checks
        checks = [
            ('database', self.check_database),
            ('redis', self.check_redis),
            ('cache', self.check_cache),
            ('disk_space', self.check_disk_space),
            ('memory', self.check_memory),
            ('gmail_api', self.check_gmail_api),
            ('external_apis', self.check_external_apis)
        ]
        
        # Run all checks
        for check_name, check_function in checks:
            try:
                check_result = check_function()
                health_status['checks'][check_name] = check_result
                
                # Update summary
                health_status['summary']['total_checks'] += 1
                if check_result['status'] == 'healthy':
                    health_status['summary']['passed'] += 1
                elif check_result['status'] == 'warning':
                    health_status['summary']['warnings'] += 1
                else:
                    health_status['summary']['failed'] += 1
                    health_status['overall_status'] = 'unhealthy'
                    
            except Exception as e:
                # If health check itself fails
                health_status['checks'][check_name] = {
                    'status': 'error',
                    'message': f'Health check failed: {str(e)}',
                    'timestamp': timezone.now().isoformat()
                }
                health_status['summary']['total_checks'] += 1
                health_status['summary']['failed'] += 1
                health_status['overall_status'] = 'unhealthy'
        
        # If we have warnings but no failures, mark as degraded
        if (health_status['summary']['warnings'] > 0 and 
            health_status['summary']['failed'] == 0 and 
            health_status['overall_status'] == 'healthy'):
            health_status['overall_status'] = 'degraded'
        
        # Add performance metrics
        total_time = (time.time() - start_time) * 1000
        health_status['performance'] = {
            'total_check_time_ms': round(total_time, 2)
        }
        
        # Log health check results
        if health_status['overall_status'] == 'unhealthy':
            self.logger.error(
                f"Health check failed: {health_status['summary']['failed']} checks failed",
                extra_context={'health_check': health_status}
            )
        elif health_status['overall_status'] == 'degraded':
            self.logger.warning(
                f"Health check degraded: {health_status['summary']['warnings']} warnings",
                extra_context={'health_check': health_status}
            )
        else:
            self.logger.info(
                "Health check passed",
                extra_context={'health_check_summary': health_status['summary']}
            )
        
        return health_status
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Test write operation
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_session")
                count = cursor.fetchone()[0]
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check if response time is acceptable
            status = 'healthy'
            message = 'Database connection successful'
            
            if duration_ms > 1000:  # 1 second
                status = 'warning'
                message = f'Database response slow: {duration_ms:.2f}ms'
            elif duration_ms > 5000:  # 5 seconds
                status = 'unhealthy'
                message = f'Database response very slow: {duration_ms:.2f}ms'
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'response_time_ms': round(duration_ms, 2),
                    'session_count': count
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Database health check failed", exception=e)
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }
    
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        try:
            # Get Redis connection from Django settings
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            
            # Test basic operations
            test_key = 'health_check_test'
            r.set(test_key, 'test_value', ex=60)
            value = r.get(test_key)
            r.delete(test_key)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = r.info('memory')
            used_memory = info.get('used_memory_human', 'Unknown')
            
            status = 'healthy'
            message = 'Redis connection successful'
            
            if duration_ms > 500:  # 500ms
                status = 'warning'
                message = f'Redis response slow: {duration_ms:.2f}ms'
            elif duration_ms > 2000:  # 2 seconds
                status = 'unhealthy'
                message = f'Redis response very slow: {duration_ms:.2f}ms'
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'response_time_ms': round(duration_ms, 2),
                    'used_memory': used_memory
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Redis health check failed", exception=e)
            return {
                'status': 'unhealthy',
                'message': f'Redis connection failed: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }
    
    def check_cache(self) -> Dict[str, Any]:
        """Check Django cache system"""
        start_time = time.time()
        
        try:
            # Test cache operations
            test_key = 'health_check_cache_test'
            test_value = 'cache_test_value'
            
            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if retrieved_value != test_value:
                return {
                    'status': 'unhealthy',
                    'message': 'Cache value mismatch',
                    'timestamp': timezone.now().isoformat()
                }
            
            status = 'healthy'
            message = 'Cache working correctly'
            
            if duration_ms > 200:  # 200ms
                status = 'warning'
                message = f'Cache response slow: {duration_ms:.2f}ms'
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'response_time_ms': round(duration_ms, 2)
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Cache health check failed", exception=e)
            return {
                'status': 'unhealthy',
                'message': f'Cache system failed: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil
            
            # Check disk space in current directory (usually where app is deployed)
            total, used, free = shutil.disk_usage('.')
            
            # Convert to GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            usage_percent = (used / total) * 100
            
            status = 'healthy'
            message = f'Disk usage: {usage_percent:.1f}% ({free_gb:.1f}GB free)'
            
            if usage_percent > 85:
                status = 'warning'
                message = f'Disk usage high: {usage_percent:.1f}% ({free_gb:.1f}GB free)'
            elif usage_percent > 95:
                status = 'unhealthy'
                message = f'Disk usage critical: {usage_percent:.1f}% ({free_gb:.1f}GB free)'
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'total_gb': round(total_gb, 2),
                    'used_gb': round(used_gb, 2),
                    'free_gb': round(free_gb, 2),
                    'usage_percent': round(usage_percent, 1)
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Could not check disk space: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }
    
    def check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            status = 'healthy'
            message = f'Memory usage: {usage_percent:.1f}% ({available_gb:.1f}GB available)'
            
            if usage_percent > 85:
                status = 'warning'
                message = f'Memory usage high: {usage_percent:.1f}% ({available_gb:.1f}GB available)'
            elif usage_percent > 95:
                status = 'unhealthy'
                message = f'Memory usage critical: {usage_percent:.1f}% ({available_gb:.1f}GB available)'
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'usage_percent': round(usage_percent, 1),
                    'available_gb': round(available_gb, 2),
                    'total_gb': round(memory.total / (1024**3), 2)
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': 'psutil not available - cannot check memory',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Could not check memory: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }
    
    def check_gmail_api(self) -> Dict[str, Any]:
        """Check Gmail API connectivity"""
        start_time = time.time()
        
        try:
            # This is a basic check - in production you'd want to test with actual credentials
            # For now, just check if we can reach Google's OAuth endpoint
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/tokeninfo',
                params={'access_token': 'invalid_token'},
                timeout=5
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # We expect a 400 error for invalid token, which means the API is reachable
            if response.status_code in [400, 401]:
                status = 'healthy'
                message = 'Gmail API reachable'
            else:
                status = 'warning'
                message = f'Gmail API returned unexpected status: {response.status_code}'
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'response_time_ms': round(duration_ms, 2)
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except requests.RequestException as e:
            return {
                'status': 'unhealthy',
                'message': f'Gmail API unreachable: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Gmail API check failed: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }
    
    def check_external_apis(self) -> Dict[str, Any]:
        """Check other external API dependencies"""
        checks = {}
        overall_status = 'healthy'
        
        # List of external APIs to check
        apis_to_check = [
            ('httpbin', 'https://httpbin.org/status/200'),  # Simple test endpoint
        ]
        
        for api_name, url in apis_to_check:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    checks[api_name] = {
                        'status': 'healthy',
                        'response_time_ms': round(duration_ms, 2)
                    }
                else:
                    checks[api_name] = {
                        'status': 'unhealthy',
                        'message': f'HTTP {response.status_code}'
                    }
                    overall_status = 'degraded'
                    
            except Exception as e:
                checks[api_name] = {
                    'status': 'unhealthy',
                    'message': str(e)
                }
                overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'message': f'External API checks: {len([c for c in checks.values() if c["status"] == "healthy"])}/{len(checks)} healthy',
            'checks': checks,
            'timestamp': timezone.now().isoformat()
        }


# Global health checker instance
health_checker = HealthChecker()


# Convenience functions
def get_system_health() -> Dict[str, Any]:
    """Get complete system health status"""
    return health_checker.check_all_systems()


def is_system_healthy() -> bool:
    """Quick check if system is healthy"""
    health = health_checker.check_all_systems()
    return health['overall_status'] == 'healthy' 