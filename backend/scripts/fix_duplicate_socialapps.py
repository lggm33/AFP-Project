#!/usr/bin/env python
"""
Script to fix duplicate SocialApp objects for Google OAuth
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

def fix_duplicate_google_apps():
    """Remove duplicate Google SocialApp objects"""
    google_apps = SocialApp.objects.filter(provider='google')
    
    print(f"Found {google_apps.count()} Google SocialApp objects:")
    
    for i, app in enumerate(google_apps):
        print(f"  {i+1}. ID: {app.id}, Name: {app.name}, Client ID: {app.client_id[:20]}...")
    
    if google_apps.count() <= 1:
        print("✅ No duplicates found!")
        return
    
    # Keep the first one and delete the rest
    first_app = google_apps.first()
    duplicates = google_apps.exclude(id=first_app.id)
    
    print(f"\n🗑️  Deleting {duplicates.count()} duplicate Google SocialApp objects...")
    deleted_count = duplicates.delete()[0]
    print(f"✅ Deleted {deleted_count} duplicate objects")
    
    # Ensure the remaining app has correct credentials
    from django.conf import settings
    google_client_id = settings.GOOGLE_CLIENT_ID
    google_client_secret = settings.GOOGLE_CLIENT_SECRET
    
    if first_app.client_id != google_client_id or first_app.secret != google_client_secret:
        print("🔧 Updating credentials of remaining SocialApp...")
        first_app.client_id = google_client_id
        first_app.secret = google_client_secret
        first_app.save()
        print("✅ Updated credentials")
    
    # Ensure it's connected to the site
    site = Site.objects.get(pk=1)
    if site not in first_app.sites.all():
        first_app.sites.add(site)
        print("✅ Connected to site")
    
    print(f"\n✅ Final configuration:")
    print(f"   Google SocialApp ID: {first_app.id}")
    print(f"   Client ID: {first_app.client_id[:20]}...")
    print(f"   Connected to site: {site.domain}")

def main():
    print("🔧 Fixing duplicate Google SocialApp objects...")
    print("=" * 60)
    
    fix_duplicate_google_apps()
    
    print("\n" + "=" * 60)
    print("✅ OAuth setup fixed!")
    print("\nYou can now try the OAuth flow again.")

if __name__ == '__main__':
    main() 