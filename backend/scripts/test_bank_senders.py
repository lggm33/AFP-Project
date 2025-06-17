#!/usr/bin/env python
"""
Test script for Bank Sender functionality
Tests the new BankSender and UserBankSender models and endpoints
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


def test_bank_sender_models():
    """Test BankSender and UserBankSender model creation and relationships"""
    print("🧪 Testing Bank Sender Models...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    print(f"✅ Test user: {user.username} ({'created' if created else 'exists'})")
    
    # Get or create test bank
    bank, created = Bank.objects.get_or_create(
        user=user,
        name='Banco Nacional',
        defaults={'country': 'CR'}
    )
    print(f"✅ Test bank: {bank.name} ({'created' if created else 'exists'})")
    
    # Create test integration
    integration, created = Integration.objects.get_or_create(
        user=user,
        provider='gmail',
        email_address='test@gmail.com',
        defaults={'is_active': True}
    )
    print(f"✅ Test integration: {integration.email_address} ({'created' if created else 'exists'})")
    
    # Create test bank sender
    bank_sender, created = BankSender.objects.get_or_create(
        bank=bank,
        sender_email='notificaciones@bncr.fi.cr',
        defaults={
            'sender_name': 'Banco Nacional Notificaciones',
            'confidence_score': 0.9,
            'created_by': user
        }
    )
    print(f"✅ Bank sender: {bank_sender.sender_email} ({'created' if created else 'exists'})")
    print(f"   - Domain: {bank_sender.sender_domain}")
    print(f"   - Confidence: {bank_sender.confidence_score}")
    print(f"   - Verified: {bank_sender.is_verified}")
    
    # Create user bank sender assignment
    user_sender, created = UserBankSender.objects.get_or_create(
        user=user,
        integration=integration,
        bank_sender=bank_sender,
        defaults={
            'is_active': True,
            'custom_name': 'Mi Banco Nacional'
        }
    )
    print(f"✅ User bank sender: {user_sender} ({'created' if created else 'exists'})")
    print(f"   - Active: {user_sender.is_active}")
    print(f"   - Display name: {user_sender.display_name}")
    print(f"   - Effective confidence: {user_sender.effective_confidence}")
    
    return user, integration, bank_sender, user_sender


def test_bank_sender_queries():
    """Test common queries for bank senders"""
    print("\n🔍 Testing Bank Sender Queries...")
    
    # Get all bank senders
    all_senders = BankSender.objects.all()
    print(f"✅ Total bank senders: {all_senders.count()}")
    
    # Get verified senders
    verified_senders = BankSender.objects.filter(is_verified=True)
    print(f"✅ Verified senders: {verified_senders.count()}")
    
    # Get senders by domain
    bncr_senders = BankSender.objects.filter(sender_domain__contains='bncr')
    print(f"✅ BNCR senders: {bncr_senders.count()}")
    
    # Get user's active senders
    user_senders = UserBankSender.objects.filter(is_active=True)
    print(f"✅ Active user senders: {user_senders.count()}")
    
    # Test relationships
    for sender in all_senders[:3]:  # Show first 3
        print(f"   📧 {sender.sender_email}")
        print(f"      Bank: {sender.bank.name}")
        print(f"      Users: {sender.user_assignments.count()}")
        print(f"      Created by: {sender.created_by.username if sender.created_by else 'N/A'}")


def test_bank_sender_search():
    """Test search functionality"""
    print("\n🔎 Testing Bank Sender Search...")
    
    # Search by email pattern
    email_search = BankSender.objects.filter(sender_email__icontains='notificacion')
    print(f"✅ Email search 'notificacion': {email_search.count()} results")
    
    # Search by domain
    domain_search = BankSender.objects.filter(sender_domain__icontains='bncr')
    print(f"✅ Domain search 'bncr': {domain_search.count()} results")
    
    # Search by bank name
    bank_search = BankSender.objects.filter(bank__name__icontains='Nacional')
    print(f"✅ Bank search 'Nacional': {bank_search.count()} results")


def create_sample_data():
    """Create sample bank senders for testing"""
    print("\n📝 Creating Sample Data...")
    
    # Get test user
    user = User.objects.get(username='test_user')
    
    # Sample Costa Rican banks and their common sender emails
    sample_banks = [
        {
            'name': 'BAC San José',
            'senders': [
                'notificacion@notificacionesbaccr.com',
                'alertas@baccredomatic.com',
                'servicios@baccredomatic.com'
            ]
        },
        {
            'name': 'Banco Popular',
            'senders': [
                'notificaciones@bancopopular.fi.cr',
                'alertas@bancopopular.fi.cr'
            ]
        },
        {
            'name': 'Scotiabank',
            'senders': [
                'notificaciones@scotiabankcr.com',
                'alertas@scotiabankcr.com'
            ]
        }
    ]
    
    created_count = 0
    for bank_data in sample_banks:
        # Get or create bank
        bank, _ = Bank.objects.get_or_create(
            user=user,
            name=bank_data['name'],
            defaults={'country': 'CR'}
        )
        
        # Create senders for this bank
        for sender_email in bank_data['senders']:
            sender, created = BankSender.objects.get_or_create(
                bank=bank,
                sender_email=sender_email,
                defaults={
                    'sender_name': f"{bank_data['name']} Notifications",
                    'confidence_score': 0.85,
                    'created_by': user
                }
            )
            if created:
                created_count += 1
                print(f"   ✅ Created: {sender.sender_email}")
    
    print(f"✅ Created {created_count} new bank senders")


def main():
    """Main test function"""
    print("🚀 Bank Sender Implementation Test")
    print("=" * 50)
    
    try:
        # Test model creation
        user, integration, bank_sender, user_sender = test_bank_sender_models()
        
        # Create sample data
        create_sample_data()
        
        # Test queries
        test_bank_sender_queries()
        
        # Test search
        test_bank_sender_search()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\n📊 Summary:")
        print(f"   - Total Banks: {Bank.objects.count()}")
        print(f"   - Total Bank Senders: {BankSender.objects.count()}")
        print(f"   - Total User Bank Senders: {UserBankSender.objects.count()}")
        print(f"   - Total Integrations: {Integration.objects.count()}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 