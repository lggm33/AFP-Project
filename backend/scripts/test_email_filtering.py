#!/usr/bin/env python
"""
Test script for Email Filtering by User Bank Senders
Tests the integration between bank senders and email filtering
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


def test_email_filtering_logic():
    """Test the email filtering logic with bank senders"""
    print("🧪 Testing Email Filtering by User Bank Senders...")
    
    # Get test user and integration
    try:
        user = User.objects.get(username='test_user')
        integration = Integration.objects.filter(user=user, provider='gmail').first()
        
        if not integration:
            print("❌ No Gmail integration found for test user")
            return False
            
        print(f"✅ Using integration: {integration.email_address}")
        
        # Get user's active bank senders
        active_senders = UserBankSender.objects.filter(
            user=user,
            integration=integration,
            is_active=True
        ).select_related('bank_sender')
        
        print(f"✅ Found {active_senders.count()} active bank senders:")
        sender_emails = []
        for user_sender in active_senders:
            sender_email = user_sender.bank_sender.sender_email
            sender_emails.append(sender_email)
            print(f"   📧 {sender_email} ({user_sender.bank_sender.bank.name})")
        
        if not sender_emails:
            print("⚠️  No active bank senders found. Creating test data...")
            create_test_bank_senders(user, integration)
            return test_email_filtering_logic()  # Retry
        
        # Test Gmail provider filtering
        provider = GmailProvider(integration)
        
        # Get recent messages (unfiltered)
        print("\n🔍 Testing email retrieval...")
        recent_messages = provider.get_recent_messages(max_results=50, days_back=30)
        print(f"✅ Total recent messages: {len(recent_messages)}")
        
        # Filter messages by user's bank senders
        filtered_messages = []
        for message in recent_messages:
            sender = message.get('sender', '').lower()
            for bank_sender_email in sender_emails:
                if bank_sender_email.lower() in sender:
                    filtered_messages.append(message)
                    break
        
        print(f"✅ Messages from user's bank senders: {len(filtered_messages)}")
        
        # Show sample filtered messages
        if filtered_messages:
            print("\n📧 Sample filtered messages:")
            for i, msg in enumerate(filtered_messages[:3]):
                print(f"   {i+1}. From: {msg['sender']}")
                print(f"      Subject: {msg['subject'][:50]}...")
                print(f"      Date: {msg['timestamp']}")
        
        # Test sender matching logic
        print("\n🎯 Testing sender matching logic:")
        test_senders = [
            "notificaciones@bncr.fi.cr",
            "alertas@bancopopular.fi.cr", 
            "notificacion@notificacionesbaccr.com",
            "random@gmail.com"
        ]
        
        for test_sender in test_senders:
            matches = any(bank_email.lower() in test_sender.lower() for bank_email in sender_emails)
            status = "✅ MATCH" if matches else "❌ NO MATCH"
            print(f"   {test_sender}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_test_bank_senders(user, integration):
    """Create test bank senders for the user"""
    print("📝 Creating test bank senders...")
    
    # Sample bank senders to create
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


def test_api_endpoint_simulation():
    """Simulate the API endpoint logic"""
    print("\n🌐 Testing API Endpoint Logic Simulation...")
    
    user = User.objects.get(username='test_user')
    integration = Integration.objects.filter(user=user, provider='gmail').first()
    
    # Simulate frontend request parameters
    filters = {
        'max_results': 20,
        'days_back': 30,
        'integration_id': integration.id,
        'only_bank_senders': True
    }
    
    print(f"📋 Simulating request with filters: {filters}")
    
    # Get user's active bank senders (like frontend does)
    active_bank_senders = UserBankSender.objects.filter(
        user=user,
        integration_id=filters['integration_id'],
        is_active=True
    ).select_related('bank_sender')
    
    if not active_bank_senders.exists():
        print("❌ No active bank senders found")
        return False
    
    # Create sender filter
    sender_emails = [ubs.bank_sender.sender_email for ubs in active_bank_senders]
    sender_filter = '|'.join(sender_emails)
    
    print(f"🎯 Generated sender filter: {sender_filter}")
    print(f"📧 Active sender emails: {sender_emails}")
    
    # Simulate email retrieval and filtering
    provider = GmailProvider(integration)
    all_messages = provider.get_recent_messages(
        max_results=filters['max_results'], 
        days_back=filters['days_back']
    )
    
    # Client-side filtering (like frontend does)
    filtered_messages = []
    for msg in all_messages:
        sender = msg.get('sender', '').lower()
        if any(bank_email.lower() in sender for bank_email in sender_emails):
            filtered_messages.append(msg)
    
    print(f"✅ Total messages: {len(all_messages)}")
    print(f"✅ Filtered messages: {len(filtered_messages)}")
    
    # Show results
    if filtered_messages:
        print("\n📊 Filtering Results:")
        sender_counts = {}
        for msg in filtered_messages:
            sender = msg['sender']
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        for sender, count in sender_counts.items():
            print(f"   📧 {sender}: {count} messages")
    
    return True


def main():
    """Main test function"""
    print("🚀 Email Filtering by Bank Senders Test")
    print("=" * 60)
    
    try:
        # Test basic filtering logic
        success1 = test_email_filtering_logic()
        
        # Test API simulation
        success2 = test_api_endpoint_simulation()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("✅ All email filtering tests completed successfully!")
            print("\n💡 Key Features Tested:")
            print("   - User-specific bank sender filtering")
            print("   - Integration-specific sender assignments")
            print("   - Client-side email filtering logic")
            print("   - Sender matching algorithms")
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