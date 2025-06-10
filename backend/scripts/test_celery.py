#!/usr/bin/env python
"""
Test script to verify Celery configuration and basic functionality.

This script tests:
1. Celery app initialization
2. Basic task execution
3. Database connectivity for queue models
4. Redis connectivity

Run this script from the backend directory:
python scripts/test_celery.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

from afp_backend.celery import app as celery_app
from banking.models import EmailQueue, EmailProcessingLog, BankTemplate
from transactions.models import TransactionReview, UserCorrection, TemplateImprovement
from django.contrib.auth.models import User
from django.utils import timezone
import json

def test_celery_configuration():
    """Test basic Celery configuration"""
    print("🔧 Testing Celery Configuration...")
    
    # Test Celery app
    print(f"✅ Celery app name: {celery_app.main}")
    print(f"✅ Celery broker URL: {celery_app.conf.broker_url}")
    print(f"✅ Celery result backend: {celery_app.conf.result_backend}")
    
    # Test task routes
    routes = celery_app.conf.task_routes
    print(f"✅ Configured task routes: {len(routes)} routes")
    for task, config in routes.items():
        print(f"   - {task} → {config['queue']}")
    
    # Test scheduled tasks
    schedule = celery_app.conf.beat_schedule
    print(f"✅ Scheduled tasks: {len(schedule)} tasks")
    for task_name, config in schedule.items():
        print(f"   - {task_name}: {config['task']}")
    
    print("✅ Celery configuration test completed!\n")

def test_debug_task():
    """Test the debug task"""
    print("🧪 Testing Debug Task...")
    
    try:
        # Import and call the debug task
        from afp_backend.celery import debug_task
        result = debug_task()
        print(f"✅ Debug task result: {result}")
    except Exception as e:
        print(f"❌ Debug task failed: {e}")
    
    print("✅ Debug task test completed!\n")

def test_database_models():
    """Test that all new models can be created and queried"""
    print("📊 Testing Database Models...")
    
    try:
        # Test EmailQueue model
        queue_count = EmailQueue.objects.count()
        print(f"✅ EmailQueue model accessible - {queue_count} records")
        
        # Test EmailProcessingLog model
        log_count = EmailProcessingLog.objects.count()
        print(f"✅ EmailProcessingLog model accessible - {log_count} records")
        
        # Test BankTemplate model
        template_count = BankTemplate.objects.count()
        print(f"✅ BankTemplate model accessible - {template_count} records")
        
        # Test TransactionReview model
        review_count = TransactionReview.objects.count()
        print(f"✅ TransactionReview model accessible - {review_count} records")
        
        # Test UserCorrection model
        correction_count = UserCorrection.objects.count()
        print(f"✅ UserCorrection model accessible - {correction_count} records")
        
        # Test TemplateImprovement model
        improvement_count = TemplateImprovement.objects.count()
        print(f"✅ TemplateImprovement model accessible - {improvement_count} records")
        
    except Exception as e:
        print(f"❌ Database model test failed: {e}")
    
    print("✅ Database models test completed!\n")

def test_health_check_task():
    """Test the health check task"""
    print("🏥 Testing Health Check Task...")
    
    try:
        from afp_backend.celery import health_check
        result = health_check()
        print(f"✅ Health check result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Health check task failed: {e}")
    
    print("✅ Health check test completed!\n")

def test_redis_connectivity():
    """Test Redis connectivity"""
    print("🔴 Testing Redis Connectivity...")
    
    try:
        import redis
        from django.conf import settings
        
        # Parse Redis URL from Celery broker URL
        broker_url = settings.CELERY_BROKER_URL
        print(f"✅ Broker URL: {broker_url}")
        
        # Try to connect to Redis
        if broker_url.startswith('redis://'):
            # Extract Redis connection details
            redis_client = redis.from_url(broker_url)
            redis_client.ping()
            print("✅ Redis connection successful!")
            
            # Test basic operations
            redis_client.set('test_key', 'test_value')
            value = redis_client.get('test_key')
            print(f"✅ Redis read/write test: {value.decode() if value else 'None'}")
            redis_client.delete('test_key')
        else:
            print(f"⚠️  Non-Redis broker detected: {broker_url}")
            
    except ImportError:
        print("❌ Redis package not installed")
    except Exception as e:
        print(f"❌ Redis connectivity test failed: {e}")
    
    print("✅ Redis connectivity test completed!\n")

def main():
    """Run all tests"""
    print("🚀 AFP Celery Configuration Test Suite")
    print("=" * 50)
    
    test_celery_configuration()
    test_debug_task()
    test_database_models()
    test_health_check_task()
    test_redis_connectivity()
    
    print("🎉 All tests completed!")
    print("\n📋 Next Steps:")
    print("1. Start Redis server: redis-server")
    print("2. Start Celery worker: celery -A afp_backend worker --loglevel=info")
    print("3. Start Celery beat: celery -A afp_backend beat --loglevel=info")
    print("4. Test with actual tasks!")

if __name__ == "__main__":
    main() 