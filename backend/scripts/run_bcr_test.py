#!/usr/bin/env python3
"""
Simple runner for BCR email analysis test
Use this to run the test with proper error handling and user input
"""

import os
import sys

def get_user_email():
    """Get user email from user input"""
    print("👤 Please provide the email of a user with Gmail OAuth configured:")
    print("   (This should be a user in your Django database with Gmail access)")
    
    user_email = input("User email: ").strip()
    
    if not user_email:
        print("❌ No email provided")
        return None
    
    if '@' not in user_email:
        print("❌ Invalid email format")
        return None
    
    return user_email

def check_openai_key():
    """Check if OpenAI API key is set"""
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please run: export OPENAI_API_KEY='your-key-here'")
        return False
    
    print(f"✅ OpenAI API key found")
    return True

def main():
    """Main execution"""
    print("🧪 BCR EMAIL ANALYSIS TEST RUNNER")
    print("=" * 40)
    
    # Check OpenAI key
    if not check_openai_key():
        return
    
    # Get user email
    user_email = get_user_email()
    if not user_email:
        return
    
    print(f"\n🚀 Starting test for user: {user_email}")
    print("=" * 50)
    
    try:
        # Import and run the test
        from test_bcr_email_analysis import SecureBCREmailAnalyzer
        
        analyzer = SecureBCREmailAnalyzer(user_email)
        analyzer.run_full_test()
        
    except ImportError as e:
        print(f"❌ Failed to import test module: {e}")
        print("Make sure you're running from the backend/scripts directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 