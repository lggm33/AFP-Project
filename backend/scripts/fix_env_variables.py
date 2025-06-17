#!/usr/bin/env python3
"""
Automatic fix script for environment variable issues
This script attempts to fix common .env problems automatically
"""

import os
import sys
import subprocess
from pathlib import Path

def install_python_dotenv():
    """Install python-dotenv if not installed"""
    try:
        import dotenv
        print("✅ python-dotenv already installed")
        return True
    except ImportError:
        print("📦 Installing python-dotenv...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-dotenv'])
            print("✅ python-dotenv installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install python-dotenv: {e}")
            return False

def create_env_file():
    """Create .env file in project root"""
    project_root = Path('/Users/gabrielgomez/Personal/afp-project')
    env_file = project_root / '.env'
    
    if env_file.exists():
        print(f"✅ .env file already exists at {env_file}")
        
        # Check if OPENAI_API_KEY is in it
        with open(env_file, 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY' in content:
                print("✅ OPENAI_API_KEY already defined in .env")
                return True
            else:
                print("⚠️  OPENAI_API_KEY not found in existing .env file")
    
    # Get API key from user
    print("\n🔑 OpenAI API Key Setup")
    print("=" * 30)
    print("Please enter your OpenAI API key:")
    print("(You can get it from: https://platform.openai.com/api-keys)")
    
    api_key = input("OpenAI API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    if not api_key.startswith('sk-'):
        print("⚠️  API key should start with 'sk-', but proceeding anyway...")
    
    # Create or append to .env file
    try:
        if env_file.exists():
            # Append to existing file
            with open(env_file, 'a') as f:
                f.write(f"\n# OpenAI API Configuration\n")
                f.write(f"OPENAI_API_KEY={api_key}\n")
            print(f"✅ Added OPENAI_API_KEY to existing {env_file}")
        else:
            # Create new file
            env_content = f"""# AFP Project Environment Variables

# OpenAI API Configuration
OPENAI_API_KEY={api_key}

# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database Configuration (if needed)
# DATABASE_URL=postgresql://user:password@localhost:5432/afp_db

# Redis Configuration (if needed)  
# REDIS_URL=redis://localhost:6379/0
"""
            
            with open(env_file, 'w') as f:
                f.write(env_content)
            print(f"✅ Created new .env file at {env_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def update_django_settings():
    """Update Django settings.py to load .env file"""
    settings_file = Path('/Users/gabrielgomez/Personal/afp-project/backend/afp_backend/settings.py')
    
    if not settings_file.exists():
        print(f"❌ Django settings.py not found at {settings_file}")
        return False
    
    # Read current settings
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Check if dotenv loading is already there
    if 'load_dotenv' in content:
        print("✅ dotenv loading already configured in settings.py")
        return True
    
    # Add dotenv loading
    dotenv_code = '''from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')

'''
    
    # Find where to insert (after initial imports)
    lines = content.split('\n')
    insert_index = 0
    
    # Find a good place to insert (after Path import or other imports)
    for i, line in enumerate(lines):
        if 'from pathlib import Path' in line:
            insert_index = i + 1
            break
        elif line.startswith('import ') or line.startswith('from '):
            insert_index = i + 1
    
    # If no imports found, insert at beginning
    if insert_index == 0:
        new_content = dotenv_code + content
    else:
        new_lines = lines[:insert_index] + [''] + dotenv_code.split('\n') + [''] + lines[insert_index:]
        new_content = '\n'.join(new_lines)
    
    # Write back
    try:
        # Backup original
        backup_file = settings_file.with_suffix('.py.backup')
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"✅ Created backup at {backup_file}")
        
        # Write updated settings
        with open(settings_file, 'w') as f:
            f.write(new_content)
        print(f"✅ Updated {settings_file} to load .env file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating settings.py: {e}")
        return False

def test_env_loading():
    """Test if environment loading works"""
    print("\n🧪 TESTING ENVIRONMENT LOADING")
    print("=" * 40)
    
    try:
        # Test python-dotenv directly
        from dotenv import load_dotenv
        
        env_file = Path('/Users/gabrielgomez/Personal/afp-project/.env')
        if env_file.exists():
            load_dotenv(env_file)
            
            key = os.getenv('OPENAI_API_KEY')
            if key:
                print(f"✅ python-dotenv successfully loaded OPENAI_API_KEY")
                print(f"   Value: {key[:10]}...{key[-4:] if len(key) > 14 else key}")
                return True
            else:
                print("❌ python-dotenv did not load OPENAI_API_KEY")
                return False
        else:
            print("❌ .env file not found for testing")
            return False
            
    except Exception as e:
        print(f"❌ Error testing environment loading: {e}")
        return False

def test_django_integration():
    """Test Django integration"""
    print("\n🧪 TESTING DJANGO INTEGRATION")
    print("=" * 40)
    
    try:
        # Add Django path
        sys.path.append('/Users/gabrielgomez/Personal/afp-project/backend')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
        
        import django
        django.setup()
        
        print("✅ Django setup successful")
        
        # Test accessing OPENAI_API_KEY
        key = os.getenv('OPENAI_API_KEY')
        if key:
            print(f"✅ OPENAI_API_KEY accessible in Django context")
            print(f"   Value: {key[:10]}...{key[-4:] if len(key) > 14 else key}")
            return True
        else:
            print("❌ OPENAI_API_KEY not accessible in Django context")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Django integration: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 AUTOMATIC .env FIX TOOL")
    print("=" * 40)
    
    success_steps = []
    
    # Step 1: Install python-dotenv
    if install_python_dotenv():
        success_steps.append("✅ python-dotenv installed")
    else:
        print("❌ Failed to install python-dotenv")
        return
    
    # Step 2: Create/update .env file
    if create_env_file():
        success_steps.append("✅ .env file configured")
    else:
        print("❌ Failed to configure .env file")
        return
    
    # Step 3: Update Django settings
    if update_django_settings():
        success_steps.append("✅ Django settings updated")
    else:
        print("❌ Failed to update Django settings")
        return
    
    # Step 4: Test environment loading
    if test_env_loading():
        success_steps.append("✅ Environment loading works")
    else:
        print("❌ Environment loading test failed")
        return
    
    # Step 5: Test Django integration
    if test_django_integration():
        success_steps.append("✅ Django integration works")
    else:
        print("❌ Django integration test failed")
        return
    
    # Summary
    print(f"\n🎉 SUCCESS! All steps completed:")
    for step in success_steps:
        print(f"   {step}")
    
    print(f"\n✅ You can now run the BCR email analysis test:")
    print(f"   cd backend/scripts")
    print(f"   python run_bcr_test.py")

if __name__ == "__main__":
    main() 