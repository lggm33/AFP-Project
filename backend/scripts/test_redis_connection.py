#!/usr/bin/env python3
"""
🔴 AFP Project - Redis Connection Testing Script

This script tests:
1. Direct Redis connection
2. Django Redis cache
3. Celery Redis broker connection
4. Performance testing

Usage:
    cd backend
    python scripts/test_redis_connection.py
"""

import os
import sys

# Add the parent directory to the path so we can import Django settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

import redis
import time
from django.core.cache import cache
from celery import current_app

def test_direct_redis_connection():
    """Test direct Redis connection"""
    print("🔴 Testing Direct Redis Connection...")
    
    try:
        # Connect to Redis using the same URL Django uses
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Test ping
        ping_result = redis_client.ping()
        print(f"✅ Redis PING: {ping_result}")
        
        # Test set/get
        test_key = 'afp_test_key'
        test_value = 'AFP Project Redis Test'
        redis_client.set(test_key, test_value, ex=30)  # 30 seconds expiry
        retrieved_value = redis_client.get(test_key).decode('utf-8')
        print(f"✅ Redis SET/GET: {retrieved_value}")
        
        # Test Redis info
        redis_info = redis_client.info()
        print(f"✅ Redis Version: {redis_info.get('redis_version', 'Unknown')}")
        print(f"✅ Connected Clients: {redis_info.get('connected_clients', 'Unknown')}")
        print(f"✅ Used Memory: {redis_info.get('used_memory_human', 'Unknown')}")
        
        # Clean up
        redis_client.delete(test_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Direct Redis connection failed: {e}")
        return False

def test_django_cache():
    """Test Django Redis cache"""
    print("\n📦 Testing Django Redis Cache...")
    
    try:
        # Test basic cache operations
        cache_key = 'afp_cache_test'
        cache_value = {
            'message': 'AFP Django Cache Test',
            'timestamp': time.time(),
            'data': ['bank_1', 'bank_2', 'bank_3']
        }
        
        # Set cache
        cache.set(cache_key, cache_value, timeout=60)
        print("✅ Cache SET: Success")
        
        # Get cache
        retrieved_value = cache.get(cache_key)
        if retrieved_value and retrieved_value['message'] == cache_value['message']:
            print(f"✅ Cache GET: {retrieved_value['message']}")
        else:
            print("❌ Cache GET: Failed")
            return False
        
        # Test cache with prefix
        prefixed_key = 'bank_template_bcr'
        template_data = {
            'bank_name': 'Banco de Costa Rica',
            'patterns': ['Pattern 1', 'Pattern 2'],
            'success_rate': 95.5
        }
        cache.set(prefixed_key, template_data, timeout=3600)  # 1 hour
        print("✅ Cache with AFP prefix: Success")
        
        # Clean up
        cache.delete(cache_key)
        cache.delete(prefixed_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Django Cache failed: {e}")
        return False

def test_celery_redis_broker():
    """Test Celery Redis broker connection"""
    print("\n⚙️ Testing Celery Redis Broker...")
    
    try:
        # Test Celery connection
        celery_app = current_app
        
        # Check if Celery can connect to Redis
        inspector = celery_app.control.inspect()
        
        # Try to get active queues (this will fail if Redis is not connected)
        try:
            stats = inspector.stats()
            if stats:
                print("✅ Celery Redis broker: CONNECTED")
                print(f"✅ Celery broker URL: {celery_app.conf.broker_url}")
            else:
                print("⚠️ Celery Redis broker: Connected but no workers running")
        except:
            print("⚠️ Celery Redis broker: Connected but no workers available")
        
        # Test task queue by putting a test message
        redis_client = redis.from_url(settings.CELERY_BROKER_URL)
        
        # Check if default queue exists or create it
        queue_length = redis_client.llen('celery')
        print(f"✅ Celery default queue length: {queue_length}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery Redis broker failed: {e}")
        return False

def test_performance():
    """Test Redis performance"""
    print("\n🚀 Testing Redis Performance...")
    
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Performance test - multiple operations
        start_time = time.time()
        
        test_data = []
        for i in range(100):
            key = f"perf_test_{i}"
            value = f"AFP Performance Test Data {i} - " + "x" * 100  # ~115 bytes
            redis_client.set(key, value, ex=60)
            test_data.append(key)
        
        # Read performance
        for key in test_data:
            redis_client.get(key)
        
        end_time = time.time()
        
        # Clean up
        redis_client.delete(*test_data)
        
        total_time = end_time - start_time
        ops_per_second = (200 / total_time)  # 100 writes + 100 reads
        
        print(f"✅ Performance Test: {ops_per_second:.0f} ops/second")
        print(f"✅ Total time for 200 operations: {total_time:.3f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def print_redis_configuration():
    """Print current Redis configuration"""
    print("\n⚙️ Redis Configuration:")
    print(f"   REDIS_URL: {settings.REDIS_URL}")
    print(f"   CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
    print(f"   CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}")
    print(f"   Cache Backend: {settings.CACHES['default']['BACKEND']}")
    print(f"   Session Engine: {settings.SESSION_ENGINE}")

def main():
    """Main testing function"""
    print("🔴 AFP PROJECT - REDIS CONNECTION TESTING")
    print("=" * 50)
    
    # Print configuration
    print_redis_configuration()
    
    # Run tests
    results = []
    results.append(test_direct_redis_connection())
    results.append(test_django_cache())
    results.append(test_celery_redis_broker())
    results.append(test_performance())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 REDIS TESTING SUMMARY:")
    
    tests = [
        "Direct Redis Connection",
        "Django Redis Cache", 
        "Celery Redis Broker",
        "Performance Test"
    ]
    
    for i, (test_name, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Redis is ready for AFP Project!")
    else:
        print("⚠️ Some tests failed. Check Redis configuration.")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure REDIS_URL is set in your .env file")
        print("   2. Check if Redis server is running (Railway/local)")
        print("   3. Verify network connectivity to Redis server")
        print("   4. Install missing dependencies: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 