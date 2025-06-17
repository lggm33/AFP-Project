#!/usr/bin/env python3
"""
Test script for the new pagination system
Tests both get_all_messages and get_banking_messages with pagination
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

from core.models import Integration, UserBankSender
from core.providers.gmail_provider import GmailProvider

def test_pagination_system():
    """Test the pagination system for email retrieval"""
    print("🔄 Testing Pagination System")
    print("=" * 50)
    
    # Get a test integration
    integration = Integration.objects.filter(
        provider='gmail',
        is_active=True
    ).first()
    
    if not integration:
        print("❌ No active Gmail integration found")
        print("Please ensure you have at least one active Gmail integration")
        return
    
    print(f"✅ Using integration: {integration.email_address}")
    
    # Test 1: Test get_all_messages with pagination
    print("\n📧 Testing get_all_messages with pagination...")
    provider = GmailProvider(integration)
    
    # Test different page sizes and pages
    test_cases = [
        {'days_back': 30, 'page': 1, 'page_size': 10},
        {'days_back': 30, 'page': 2, 'page_size': 10},
        {'days_back': 7, 'page': 1, 'page_size': 5},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test Case {i}: {test_case}")
        try:
            result = provider.get_all_messages(**test_case)
            
            if 'error' in result:
                print(f"    ❌ Error: {result['error']}")
                continue
            
            print(f"    ✅ Success!")
            print(f"    📊 Total Count: {result['total_count']}")
            print(f"    📄 Current Page: {result['page']}/{result['total_pages']}")
            print(f"    📝 Messages in Page: {len(result['messages'])}")
            print(f"    ⏭️  Has Next: {result['has_next']}")
            print(f"    ⏮️  Has Previous: {result['has_previous']}")
            
            # Validate pagination logic
            expected_messages = min(test_case['page_size'], 
                                  max(0, result['total_count'] - (test_case['page'] - 1) * test_case['page_size']))
            
            if len(result['messages']) == expected_messages:
                print(f"    ✅ Pagination logic correct")
            else:
                print(f"    ❌ Pagination logic error: expected {expected_messages}, got {len(result['messages'])}")
            
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
    
    # Test 2: Test get_banking_messages with pagination
    print("\n🏦 Testing get_banking_messages with pagination...")
    
    # Get user's bank senders
    user_bank_senders = UserBankSender.objects.filter(
        user=integration.user,
        integration=integration,
        is_active=True
    ).select_related('bank_sender')
    
    if not user_bank_senders.exists():
        print("❌ No active bank senders found for this integration")
        print("Please configure some bank senders first")
        return
    
    bank_sender_emails = [ubs.bank_sender.sender_email for ubs in user_bank_senders]
    print(f"✅ Using {len(bank_sender_emails)} bank senders:")
    for email in bank_sender_emails:
        print(f"    - {email}")
    
    banking_test_cases = [
        {'days_back': 30, 'page': 1, 'page_size': 5, 'user_bank_senders': bank_sender_emails},
        {'days_back': 30, 'page': 2, 'page_size': 5, 'user_bank_senders': bank_sender_emails},
    ]
    
    for i, test_case in enumerate(banking_test_cases, 1):
        print(f"\n  Banking Test Case {i}: page={test_case['page']}, page_size={test_case['page_size']}")
        try:
            result = provider.get_banking_messages(**test_case)
            
            if 'error' in result:
                print(f"    ❌ Error: {result['error']}")
                continue
            
            print(f"    ✅ Success!")
            print(f"    📊 Total Banking Messages: {result['total_count']}")
            print(f"    📄 Current Page: {result['page']}/{result['total_pages']}")
            print(f"    📝 Messages in Page: {len(result['messages'])}")
            print(f"    ⏭️  Has Next: {result['has_next']}")
            print(f"    ⏮️  Has Previous: {result['has_previous']}")
            
            # Show sample messages
            if result['messages']:
                print(f"    📧 Sample messages:")
                for msg in result['messages'][:3]:  # Show first 3
                    print(f"      - From: {msg['sender']}")
                    print(f"        Subject: {msg['subject'][:50]}...")
            
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
    
    # Test 3: Test edge cases
    print("\n🧪 Testing edge cases...")
    
    edge_cases = [
        {'days_back': 30, 'page': 999, 'page_size': 10},  # Page out of range
        {'days_back': 30, 'page': 0, 'page_size': 10},    # Invalid page
        {'days_back': 30, 'page': 1, 'page_size': 0},     # Invalid page size
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n  Edge Case {i}: {test_case}")
        try:
            result = provider.get_all_messages(**test_case)
            
            if test_case['page'] == 999:
                # Should return empty results but valid pagination info
                if result['messages'] == [] and result['total_count'] >= 0:
                    print(f"    ✅ Correctly handled out-of-range page")
                else:
                    print(f"    ❌ Unexpected result for out-of-range page")
            
            print(f"    📊 Result: {len(result['messages'])} messages, page {result['page']}")
            
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Pagination system testing completed!")

if __name__ == "__main__":
    test_pagination_system() 