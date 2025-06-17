#!/usr/bin/env python
"""
Test script for Updated Email System
Tests the new get_all_messages and get_banking_messages methods
"""

import os
import sys
import django
from django.conf import settings

# Add the parent directory to the path so we can import Django modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

from django.contrib.auth.models import User
from banking.models import Bank
from core.models import Integration, BankSender, UserBankSender
from core.providers.gmail_provider import GmailProvider


def test_get_all_messages():
    """Test the new get_all_messages method"""
    print("🧪 Testing get_all_messages method...")
    
    try:
        user = User.objects.get(username='test_user')
        integration = Integration.objects.filter(user=user, provider='gmail').first()
        
        if not integration:
            print("❌ No Gmail integration found")
            return False
            
        print(f"✅ Using integration: {integration.email_address}")
        
        provider = GmailProvider(integration)
        
        # Test 1: Get all messages without filter
        print("\n📧 Test 1: All messages (last 7 days)")
        messages = provider.get_all_messages(max_results=20, days_back=7)
        print(f"✅ Retrieved {len(messages)} messages")
        
        # Test 2: Get messages with sender filter
        print("\n📧 Test 2: Messages with sender filter")
        messages_filtered = provider.get_all_messages(
            max_results=20, 
            days_back=7, 
            sender_filter="@gmail.com"
        )
        print(f"✅ Retrieved {len(messages_filtered)} messages with @gmail.com filter")
        
        # Test 3: Get messages with multiple sender filter
        print("\n📧 Test 3: Messages with multiple sender filter")
        messages_multi = provider.get_all_messages(
            max_results=20, 
            days_back=7, 
            sender_filter="@gmail.com|@yahoo.com"
        )
        print(f"✅ Retrieved {len(messages_multi)} messages with multiple sender filter")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_get_banking_messages():
    """Test the new get_banking_messages method with user bank senders"""
    print("\n🏦 Testing get_banking_messages method...")
    
    try:
        user = User.objects.get(username='test_user')
        integration = Integration.objects.filter(user=user, provider='gmail').first()
        
        if not integration:
            print("❌ No Gmail integration found")
            return False
        
        # Get user's active bank senders
        active_senders = UserBankSender.objects.filter(
            user=user,
            integration=integration,
            is_active=True
        ).select_related('bank_sender')
        
        user_bank_senders = [ubs.bank_sender.sender_email for ubs in active_senders]
        print(f"✅ User has {len(user_bank_senders)} active bank senders:")
        for sender in user_bank_senders:
            print(f"   📧 {sender}")
        
        if not user_bank_senders:
            print("⚠️  No active bank senders found. Creating test data...")
            create_test_bank_senders(user, integration)
            return test_get_banking_messages()  # Retry
        
        provider = GmailProvider(integration)
        
        # Test banking messages with user's senders
        print(f"\n🔍 Testing banking messages with user's {len(user_bank_senders)} senders...")
        banking_messages = provider.get_banking_messages(
            max_results=50,
            days_back=30,
            user_bank_senders=user_bank_senders
        )
        
        print(f"✅ Retrieved {len(banking_messages)} banking messages")
        
        # Show sample messages
        if banking_messages:
            print("\n📊 Sample banking messages:")
            for i, msg in enumerate(banking_messages[:3]):
                print(f"   {i+1}. From: {msg['sender']}")
                print(f"      Subject: {msg['subject'][:50]}...")
                print(f"      Date: {msg['timestamp']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def create_test_bank_senders(user, integration):
    """Create test bank senders if none exist"""
    print("📝 Creating test bank senders...")
    
    test_senders = [
        {
            'bank_name': 'Banco Nacional',
            'sender_email': 'notificaciones@bncr.fi.cr',
            'sender_name': 'BNCR Notificaciones'
        },
        {
            'bank_name': 'BAC San José',
            'sender_email': 'notificacion@notificacionesbaccr.com',
            'sender_name': 'BAC Notificaciones'
        }
    ]
    
    for sender_data in test_senders:
        # Get or create bank
        bank, _ = Bank.objects.get_or_create(
            user=user,
            name=sender_data['bank_name'],
            defaults={'country': 'CR'}
        )
        
        # Get or create bank sender
        bank_sender, created = BankSender.objects.get_or_create(
            bank=bank,
            sender_email=sender_data['sender_email'],
            defaults={
                'sender_name': sender_data['sender_name'],
                'created_by': user
            }
        )
        
        # Create user bank sender assignment
        user_sender, created = UserBankSender.objects.get_or_create(
            user=user,
            integration=integration,
            bank_sender=bank_sender,
            defaults={'is_active': True}
        )
        
        if created:
            print(f"   ✅ Created: {sender_data['sender_email']}")


def test_date_filtering():
    """Test date filtering functionality"""
    print("\n📅 Testing date filtering...")
    
    try:
        user = User.objects.get(username='test_user')
        integration = Integration.objects.filter(user=user, provider='gmail').first()
        
        if not integration:
            print("❌ No Gmail integration found")
            return False
        
        provider = GmailProvider(integration)
        
        # Test different date ranges
        date_ranges = [1, 3, 7, 30]
        
        for days in date_ranges:
            messages = provider.get_all_messages(max_results=10, days_back=days)
            print(f"✅ Last {days} days: {len(messages)} messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_api_endpoints_simulation():
    """Simulate the API endpoints with new parameters"""
    print("\n🌐 Testing API Endpoints Simulation...")
    
    try:
        user = User.objects.get(username='test_user')
        integration = Integration.objects.filter(user=user, provider='gmail').first()
        
        # Simulate frontend requests
        test_cases = [
            {
                'name': 'All messages with sender filter',
                'params': {
                    'max_results': 20,
                    'days_back': 7,
                    'sender_filter': '@gmail.com'
                },
                'endpoint': 'all_messages'
            },
            {
                'name': 'Banking messages only',
                'params': {
                    'max_results': 20,
                    'days_back': 30,
                    'only_bank_senders': True
                },
                'endpoint': 'banking_messages'
            },
            {
                'name': 'All messages last 2 days',
                'params': {
                    'max_results': 50,
                    'days_back': 2
                },
                'endpoint': 'all_messages'
            }
        ]
        
        provider = GmailProvider(integration)
        
        for test_case in test_cases:
            print(f"\n🧪 {test_case['name']}:")
            params = test_case['params']
            
            if test_case['endpoint'] == 'all_messages':
                messages = provider.get_all_messages(
                    max_results=params['max_results'],
                    days_back=params['days_back'],
                    sender_filter=params.get('sender_filter')
                )
            else:  # banking_messages
                # Get user's bank senders
                active_senders = UserBankSender.objects.filter(
                    user=user,
                    integration=integration,
                    is_active=True
                ).select_related('bank_sender')
                user_bank_senders = [ubs.bank_sender.sender_email for ubs in active_senders]
                
                messages = provider.get_banking_messages(
                    max_results=params['max_results'],
                    days_back=params['days_back'],
                    user_bank_senders=user_bank_senders
                )
            
            print(f"   ✅ Retrieved {len(messages)} messages")
            print(f"   📋 Parameters: {params}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Updated Email System Test")
    print("=" * 50)
    
    try:
        # Test new methods
        success1 = test_get_all_messages()
        success2 = test_get_banking_messages()
        success3 = test_date_filtering()
        success4 = test_api_endpoints_simulation()
        
        if all([success1, success2, success3, success4]):
            print("\n" + "=" * 50)
            print("✅ All updated email system tests completed successfully!")
            print("\n💡 New Features Tested:")
            print("   - get_all_messages with sender filtering")
            print("   - get_banking_messages with user bank senders")
            print("   - Precise date range filtering")
            print("   - Multiple sender filtering with | operator")
            print("   - API endpoint simulation")
        else:
            print("\n❌ Some tests failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 