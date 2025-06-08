#!/usr/bin/env python
"""
Script to debug OAuth flow issues
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append('/Users/gabrielgomez/Personal/afp-project/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')

django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib.sessions.models import Session
from django.utils import timezone

def debug_oauth_status():
    """Debug the current OAuth setup"""
    print("🔍 Debugging OAuth Flow Status")
    print("=" * 50)
    
    # Check user
    try:
        user = User.objects.get(email='luisggm33@gmail.com')
        print(f"✅ User found: {user.username} ({user.email})")
        print(f"   - ID: {user.id}")
        print(f"   - Superuser: {user.is_superuser}")
        print(f"   - Active: {user.is_active}")
        print(f"   - Last login: {user.last_login}")
    except User.DoesNotExist:
        print("❌ User not found")
        return
    
    # Check social accounts
    social_accounts = SocialAccount.objects.filter(user=user)
    print(f"\n📱 Social Accounts: {social_accounts.count()}")
    for acc in social_accounts:
        print(f"   - Provider: {acc.provider}")
        print(f"   - UID: {acc.uid}")
        print(f"   - Last login: {acc.last_login}")
        print(f"   - Extra data: {acc.extra_data.get('email', 'No email')}")
    
    # Check social apps
    google_apps = SocialApp.objects.filter(provider='google')
    print(f"\n🔧 Google SocialApps: {google_apps.count()}")
    for app in google_apps:
        print(f"   - ID: {app.id}")
        print(f"   - Name: {app.name}")
        print(f"   - Client ID: {app.client_id[:20]}...")
        print(f"   - Sites: {[site.domain for site in app.sites.all()]}")
    
    # Check recent sessions
    recent_sessions = Session.objects.filter(
        expire_date__gte=timezone.now()
    ).order_by('-expire_date')[:5]
    
    print(f"\n🍪 Active Sessions: {recent_sessions.count()}")
    for session in recent_sessions:
        print(f"   - Key: {session.session_key[:10]}...")
        print(f"   - Expires: {session.expire_date}")
    
    print("\n" + "=" * 50)
    print("✅ Debug completed!")

if __name__ == '__main__':
    debug_oauth_status() 