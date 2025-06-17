#!/usr/bin/env python
"""
Migration script: SocialAccount/SocialToken → Integration
Migrates existing OAuth tokens to new Integration model
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/gabrielgomez/Personal/afp-project/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken
from core.models import Integration

def migrate_oauth_tokens():
    """Migrate OAuth tokens from django-allauth to Integration model"""
    
    print("🔄 Starting OAuth token migration...")
    print("=" * 50)
    
    # Get all social accounts
    social_accounts = SocialAccount.objects.all()
    
    if not social_accounts.exists():
        print("❌ No social accounts found to migrate")
        return
    
    migrated_count = 0
    
    for social_account in social_accounts:
        try:
            user = social_account.user
            provider = social_account.provider
            email_address = social_account.extra_data.get('email')
            
            if not email_address:
                print(f"⚠️ Skipping {user.username} - no email in social account")
                continue
            
            print(f"\n👤 Migrating {user.username} ({provider})")
            print(f"   Email: {email_address}")
            
            # Check if Integration already exists
            existing_integration = Integration.objects.filter(
                user=user,
                provider=provider,
                email_address=email_address
            ).first()
            
            if existing_integration:
                print(f"   ✅ Integration already exists (ID: {existing_integration.id})")
                continue
            
            # Get OAuth tokens
            social_token = SocialToken.objects.filter(
                account=social_account,
                app__provider=provider
            ).first()
            
            if not social_token:
                print(f"   ❌ No OAuth token found for {provider}")
                continue
            
            # Prepare OAuth tokens for Integration
            oauth_tokens = {
                'access_token': social_token.token,
                'refresh_token': social_token.token_secret,
                'client_id': social_token.app.client_id,
                'client_secret': social_token.app.secret,
                'expires_at': social_token.expires_at.isoformat() if social_token.expires_at else None,
                'scope': 'https://www.googleapis.com/auth/gmail.readonly',  # Gmail scope
                'migrated_from': 'django-allauth',
                'migration_date': django.utils.timezone.now().isoformat()
            }
            
            # Create Integration
            integration = Integration.objects.create(
                user=user,
                provider=provider,
                email_address=email_address,
                is_active=True,
                provider_config={
                    'oauth_tokens': oauth_tokens,
                    'social_account_uid': social_account.uid,
                    'extra_data': social_account.extra_data
                },
                updated_by=user,
                updated_message=f"Migrated from django-allauth SocialAccount"
            )
            
            print(f"   ✅ Created Integration (ID: {integration.id})")
            print(f"   📧 OAuth tokens migrated successfully")
            
            migrated_count += 1
            
        except Exception as e:
            print(f"   ❌ Error migrating {user.username}: {str(e)}")
            continue
    
    print("\n" + "=" * 50)
    print(f"🎉 Migration completed!")
    print(f"   📊 Accounts processed: {social_accounts.count()}")
    print(f"   ✅ Successfully migrated: {migrated_count}")
    print(f"   📋 Integrations total: {Integration.objects.count()}")
    
    # Show final state
    print(f"\n📋 Final Integration state:")
    for integration in Integration.objects.all():
        print(f"   - {integration.user.username}: {integration.email_address} ({integration.provider})")

def test_gmail_provider():
    """Test GmailProvider with migrated Integration"""
    from core.providers.gmail_provider import GmailProvider
    
    print("\n🧪 Testing GmailProvider with migrated tokens...")
    print("=" * 50)
    
    gmail_integrations = Integration.objects.filter(provider='gmail')
    
    if not gmail_integrations.exists():
        print("❌ No Gmail integrations found to test")
        return
    
    for integration in gmail_integrations:
        print(f"\n👤 Testing {integration.user.username}")
        print(f"   Email: {integration.email_address}")
        
        try:
            provider = GmailProvider(integration)
            result = provider.test_connection()
            
            if result['success']:
                print(f"   ✅ Gmail connection successful")
                print(f"   📧 Email: {result['email']}")
                print(f"   📊 Messages: {result['messages_total']}")
            else:
                print(f"   ❌ Gmail connection failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Provider error: {str(e)}")

if __name__ == "__main__":
    migrate_oauth_tokens()
    test_gmail_provider() 