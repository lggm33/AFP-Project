#!/usr/bin/env python
import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
from django.contrib.auth.models import User

print('=== OAUTH DEBUGGING ===')
print()

# Check users
users = User.objects.all()
print(f'Total users: {users.count()}')
for user in users:
    print(f'  User: {user.username} (ID: {user.id})')
print()

# Check social accounts
social_accounts = SocialAccount.objects.all()
print(f'Total social accounts: {social_accounts.count()}')
for account in social_accounts:
    print(f'  Social Account: {account.provider} - User: {account.user.username} - UID: {account.uid}')
print()

# Check social tokens
social_tokens = SocialToken.objects.all()
print(f'Total social tokens: {social_tokens.count()}')
for token in social_tokens:
    print(f'  Token: {token.app.provider} - User: {token.account.user.username}')
    print(f'    Has access token: {bool(token.token)}')
    print(f'    Has refresh token: {bool(token.token_secret)}')
    print(f'    App client_id: {token.app.client_id[:20]}...')
    print(f'    App has secret: {bool(token.app.secret)}')
    print()

# Check social apps
social_apps = SocialApp.objects.all()
print(f'Total social apps: {social_apps.count()}')
for app in social_apps:
    print(f'  App: {app.provider} - Client ID: {app.client_id[:20]}... - Has Secret: {bool(app.secret)}')
print()

# Try to initialize Gmail service
print('=== GMAIL SERVICE TEST ===')
if users.exists():
    user = users.first()
    print(f'Testing Gmail service for user: {user.username}')
    
    try:
        from core.gmail_service import GmailService
        gmail_service = GmailService(user)
        
        if gmail_service.service:
            print('✅ Gmail service initialized successfully')
            result = gmail_service.test_connection()
            print(f'Connection test result: {result}')
        else:
            print('❌ Gmail service failed to initialize')
            print('Checking prerequisites...')
            
            # Check Google account
            google_account = SocialAccount.objects.filter(
                user=user,
                provider='google'
            ).first()
            
            if not google_account:
                print('  ❌ No Google social account found')
            else:
                print(f'  ✅ Google account found: {google_account.uid}')
                
                # Check token
                social_token = SocialToken.objects.filter(
                    account=google_account,
                    app__provider='google'
                ).first()
                
                if not social_token:
                    print('  ❌ No OAuth token found')
                else:
                    print('  ✅ OAuth token found')
                    print(f'    Access token length: {len(social_token.token) if social_token.token else 0}')
                    print(f'    Refresh token length: {len(social_token.token_secret) if social_token.token_secret else 0}')
                    
    except Exception as e:
        print(f'❌ Error testing Gmail service: {str(e)}')
        import traceback
        traceback.print_exc()
else:
    print('No users found') 