#!/usr/bin/env python
"""
Script to fix OAuth setup issues
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append('/Users/gabrielgomez/Personal/afp-project/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')

django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def fix_site_configuration():
    """Fix Site configuration for allauth"""
    try:
        site = Site.objects.get(pk=1)
        print(f"✅ Site exists: {site.domain} - {site.name}")
        
        # Update site to use correct domain
        if site.domain != '127.0.0.1:8000':
            site.domain = '127.0.0.1:8000'
            site.name = 'AFP Project Dev'
            site.save()
            print(f"✅ Updated site domain to: {site.domain}")
            
    except Site.DoesNotExist:
        print("❌ Site does not exist - creating one")
        site = Site.objects.create(pk=1, domain='127.0.0.1:8000', name='AFP Project Dev')
        print(f"✅ Created site: {site.domain} - {site.name}")
    
    return site

def fix_social_app():
    """Fix Social App configuration"""
    from django.conf import settings
    
    google_client_id = settings.GOOGLE_CLIENT_ID
    google_client_secret = settings.GOOGLE_CLIENT_SECRET
    
    if not google_client_id or not google_client_secret:
        print("❌ Google OAuth credentials not found in settings")
        return None
    
    print(f"✅ Google Client ID: {google_client_id[:20]}...")
    print(f"✅ Google Client Secret: {google_client_secret[:10]}...")
    
    # Check if SocialApp exists
    try:
        social_app = SocialApp.objects.get(provider='google')
        print(f"✅ Google SocialApp exists: {social_app.name}")
        
        # Update if needed
        if social_app.client_id != google_client_id:
            social_app.client_id = google_client_id
            social_app.secret = google_client_secret
            social_app.save()
            print("✅ Updated Google SocialApp credentials")
            
        # Ensure it's connected to the site
        site = Site.objects.get(pk=1)
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            print("✅ Connected Google SocialApp to site")
            
    except SocialApp.DoesNotExist:
        print("❌ Google SocialApp does not exist - creating one")
        site = Site.objects.get(pk=1)
        social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id=google_client_id,
            secret=google_client_secret,
        )
        social_app.sites.add(site)
        print("✅ Created Google SocialApp")
    
    return social_app

def main():
    print("🔧 Fixing OAuth setup...")
    print("=" * 50)
    
    # Step 1: Fix Site configuration
    print("\n1. Fixing Site configuration...")
    site = fix_site_configuration()
    
    # Step 2: Fix Social App configuration
    print("\n2. Fixing Social App configuration...")
    social_app = fix_social_app()
    
    print("\n" + "=" * 50)
    print("✅ OAuth setup completed!")
    print("\nNext steps:")
    print("1. Try the OAuth flow again")
    print("2. Check the Django server logs for any errors")

if __name__ == '__main__':
    main() 