"""
Setup script for BCR email analysis test environment
This script helps configure the necessary dependencies and environment
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing required dependencies...")
    
    dependencies = [
        'openai>=1.0.0',  # Latest version with gpt-4o support
        'beautifulsoup4',
        'lxml',
        'bleach',
        'html5lib'
    ]
    
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    return True

def check_environment():
    """Check if environment is properly configured"""
    print("\n🔍 Checking environment configuration...")
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set it with: export OPENAI_API_KEY='your-api-key'")
        return False
    else:
        print(f"✅ OpenAI API key found (ends with: ...{openai_key[-4:]})")
    
    # Check Django settings
    try:
        sys.path.append('/Users/gabrielgomez/Personal/afp-project/backend')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
        
        import django
        django.setup()
        
        from django.contrib.auth.models import User
        print("✅ Django setup successful")
        
        # Check if we have users
        user_count = User.objects.count()
        print(f"✅ Found {user_count} users in database")
        
        if user_count == 0:
            print("⚠️  No users found. You may need to create a test user.")
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False
    
    return True

def create_test_user():
    """Create a test user if needed"""
    print("\n👤 Creating test user...")
    
    try:
        from django.contrib.auth.models import User
        
        # Check if test user exists
        test_email = "test@afp-project.com"
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'username': 'test_user',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created test user: {test_email}")
        else:
            print(f"✅ Test user already exists: {test_email}")
        
        return test_email
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return None

def show_usage_instructions(test_email):
    """Show instructions for using the test script"""
    print("\n📋 USAGE INSTRUCTIONS")
    print("=" * 50)
    print(f"1. Update the test script USER_EMAIL to: {test_email}")
    print("2. Make sure you have Gmail OAuth set up for this user")
    print("3. Run the test script:")
    print("   cd backend/scripts")
    print("   python test_bcr_email_analysis.py")
    print()
    print("📝 What the test will do:")
    print("   • Connect to Gmail API")
    print("   • Search for emails from bcrtarjestcta@bancobcr.com")
    print("   • Take the first email found")
    print("   • Use OpenAI to generate CSS selectors")
    print("   • Test the selectors on the email HTML")
    print("   • Show detailed results for each step")
    print()
    print("🔧 Required setup:")
    print("   • OPENAI_API_KEY environment variable")
    print("   • Gmail OAuth tokens for the test user")
    print("   • At least one email from BCR in the Gmail account")

def main():
    """Main setup function"""
    print("🚀 AFP EMAIL ANALYSIS TEST SETUP")
    print("=" * 40)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return
    
    # Create test user
    test_email = create_test_user()
    if not test_email:
        print("❌ Failed to create test user")
        return
    
    # Show usage instructions
    show_usage_instructions(test_email)
    
    print("\n✅ Setup completed successfully!")
    print("🎯 Next: Configure Gmail OAuth and run the test")

if __name__ == "__main__":
    main() 