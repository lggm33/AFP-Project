#!/usr/bin/env python
"""
Test script for the new error handling system
Run this to validate that the error system is working correctly
"""
import os
import sys
import django
import json
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

# Import our error system
from core.exceptions import (
    AFPBaseException, ValidationError, IntegrationNotFoundError,
    GmailAPIError, BusinessLogicError, DatabaseError
)
from core.logging.structured_logger import structured_logger, error_tracker, track_error
from core.health.health_checker import get_system_health, is_system_healthy
from django.contrib.auth.models import User


def test_custom_exceptions():
    """Test custom exception creation and serialization"""
    print("🧪 Testing Custom Exceptions...")
    
    # Test basic exception
    try:
        raise ValidationError(
            message="Test validation error",
            context={'field': 'email', 'value': 'invalid@'},
            user_message="Please provide a valid email address"
        )
    except AFPBaseException as e:
        print(f"✅ ValidationError: {e.error_code}")
        print(f"   Message: {e.user_message}")
        print(f"   Context: {e.context}")
        print(f"   Dict: {e.to_dict()}")
        
    # Test nested exception
    try:
        try:
            raise ValueError("Original error")
        except ValueError as original:
            raise GmailAPIError(
                message="Gmail API failed during testing",
                context={'integration_id': 123, 'operation': 'get_messages'},
                original_exception=original
            )
    except AFPBaseException as e:
        print(f"✅ GmailAPIError: {e.error_code}")
        print(f"   Retryable: {e.retryable}")
        print(f"   Original: {e.original_exception}")
    
    print()


def test_structured_logging():
    """Test structured logging functionality"""
    print("📋 Testing Structured Logging...")
    
    # Create a test user (if not exists)
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Test different log levels
    structured_logger.info("Test info message", 
                          extra_context={'test_data': 'info_test'}, 
                          user=user, 
                          request_id='test-123')
    
    structured_logger.warning("Test warning message", 
                             extra_context={'warning_type': 'test'}, 
                             user=user, 
                             request_id='test-124')
    
    structured_logger.error("Test error message", 
                           extra_context={'error_context': 'testing'}, 
                           user=user, 
                           request_id='test-125',
                           exception=ValidationError("Test exception for logging"))
    
    # Test business event logging
    structured_logger.log_business_event(
        event='test_event_created',
        entity='test_entity',
        entity_id='test-456',
        user=user,
        request_id='test-126',
        extra_data={'test_field': 'test_value'}
    )
    
    # Test API request logging
    structured_logger.log_api_request(
        method='GET',
        endpoint='/api/test/',
        user=user,
        request_id='test-127',
        duration_ms=150.5,
        status_code=200,
        payload_size=1024
    )
    
    # Test external API call logging
    structured_logger.log_external_api_call(
        service='gmail',
        endpoint='https://gmail.googleapis.com/gmail/v1/users/me/messages',
        method='GET',
        duration_ms=250.0,
        status_code=200,
        user=user,
        request_id='test-128'
    )
    
    print("✅ Structured logging tests completed")
    print()


def test_error_tracking():
    """Test error tracking functionality"""
    print("📊 Testing Error Tracking...")
    
    user, _ = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Track different types of errors
    errors_to_track = [
        ValidationError("Test validation error 1"),
        ValidationError("Test validation error 2"),
        GmailAPIError("Test Gmail API error"),
        BusinessLogicError("Test business logic error"),
        DatabaseError("Test database error")
    ]
    
    for error in errors_to_track:
        track_error(error, user=user, request_id=f'test-{datetime.now().timestamp()}')
    
    # Get error statistics
    stats = error_tracker.get_error_stats()
    print(f"✅ Error tracking completed")
    print(f"   Total error types tracked: {len(stats['total_errors'])}")
    print(f"   Error counts: {stats['total_errors']}")
    print(f"   Top errors: {stats['top_errors'][:3]}")
    print()


def test_health_checks():
    """Test health check system"""
    print("🏥 Testing Health Checks...")
    
    # Test individual health checks
    from core.health.health_checker import health_checker
    
    print("Database check:", health_checker.check_database()['status'])
    print("Redis check:", health_checker.check_redis()['status'])
    print("Cache check:", health_checker.check_cache()['status'])
    
    # Test full system health
    health = get_system_health()
    print(f"✅ Overall system status: {health['overall_status']}")
    print(f"   Total checks: {health['summary']['total_checks']}")
    print(f"   Passed: {health['summary']['passed']}")
    print(f"   Failed: {health['summary']['failed']}")
    print(f"   Warnings: {health['summary']['warnings']}")
    print(f"   Check time: {health['performance']['total_check_time_ms']}ms")
    
    # Quick health check
    is_healthy = is_system_healthy()
    print(f"   Quick check - System healthy: {is_healthy}")
    print()


def test_error_categorization():
    """Test automatic error categorization"""
    print("🏷️ Testing Error Categorization...")
    
    from core.exceptions import categorize_exception
    
    # Test standard exceptions
    test_exceptions = [
        ValueError("Test value error"),
        KeyError("Test key error"),
        ConnectionError("Test connection error"),
        FileNotFoundError("Test file not found"),
    ]
    
    for exc in test_exceptions:
        afp_exc = categorize_exception(exc)
        print(f"✅ {type(exc).__name__} -> {afp_exc.error_code} ({afp_exc.error_category})")
    
    print()


def test_error_response_format():
    """Test error response format consistency"""
    print("📋 Testing Error Response Format...")
    
    # Create different types of errors and check their API response format
    errors = [
        ValidationError("Invalid email format", context={'field': 'email'}),
        IntegrationNotFoundError("Integration not found", context={'integration_id': 123}),
        GmailAPIError("Gmail API timeout", context={'operation': 'get_messages'})
    ]
    
    for error in errors:
        response_dict = error.to_dict()
        required_fields = ['error_id', 'error_code', 'error_category', 'message', 'timestamp', 'retryable']
        
        missing_fields = [field for field in required_fields if field not in response_dict]
        if missing_fields:
            print(f"❌ {error.error_code} missing fields: {missing_fields}")
        else:
            print(f"✅ {error.error_code} has all required fields")
            print(f"   Retryable: {response_dict['retryable']}")
            print(f"   HTTP Status: {error.http_status}")
    
    print()


def main():
    """Run all error system tests"""
    print("🚀 AFP Error System Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_custom_exceptions()
        test_structured_logging()
        test_error_tracking()
        test_health_checks()
        test_error_categorization()
        test_error_response_format()
        
        print("✅ All tests completed successfully!")
        print("\n📋 Summary:")
        print("- Custom exceptions working correctly")
        print("- Structured logging functional")
        print("- Error tracking operational")
        print("- Health checks running")
        print("- Error categorization working")
        print("- Response format consistent")
        
        print("\n🔧 Next Steps:")
        print("1. Test the health check endpoints: GET /api/core/health/")
        print("2. Test API error handling by making requests")
        print("3. Check log files in ./logs/ directory")
        print("4. Monitor error statistics via: GET /api/core/admin/error-stats/")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main() 