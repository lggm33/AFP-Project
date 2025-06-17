#!/usr/bin/env python3
"""
Diagnostic script for environment variable issues
This script helps identify why OPENAI_API_KEY is not being loaded
"""

import os
import sys
from pathlib import Path

def check_env_file_locations():
    """Check for .env files in common locations"""
    print("🔍 CHECKING .env FILE LOCATIONS")
    print("=" * 50)
    
    # Possible .env locations
    possible_locations = [
        Path.cwd() / '.env',                                    # Current directory
        Path.cwd().parent / '.env',                            # Parent directory
        Path('/Users/gabrielgomez/Personal/afp-project/.env'),  # Project root
        Path('/Users/gabrielgomez/Personal/afp-project/backend/.env'),  # Backend dir
    ]
    
    env_files_found = []
    
    for location in possible_locations:
        if location.exists():
            print(f"✅ Found .env at: {location}")
            env_files_found.append(location)
            
            # Show contents (safely)
            try:
                with open(location, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    print(f"   📄 Contents ({len(lines)} lines):")
                    for line in lines[:10]:  # Show first 10 lines
                        if 'OPENAI_API_KEY' in line:
                            # Mask the actual key
                            parts = line.split('=')
                            if len(parts) >= 2:
                                key_part = parts[1][:10] + '...' if len(parts[1]) > 10 else parts[1]
                                print(f"      🔑 {parts[0]}={key_part}")
                            else:
                                print(f"      ⚠️  {line}")
                        elif line.strip() and not line.startswith('#'):
                            print(f"      📝 {line}")
                    if len(lines) > 10:
                        print(f"      ... and {len(lines) - 10} more lines")
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
        else:
            print(f"❌ Not found: {location}")
    
    print(f"\n📊 Summary: Found {len(env_files_found)} .env files")
    return env_files_found

def check_environment_variables():
    """Check current environment variables"""
    print("\n🔍 CHECKING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    # Check OPENAI_API_KEY
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OPENAI_API_KEY found in environment")
        print(f"   Value: {openai_key[:10]}...{openai_key[-4:] if len(openai_key) > 14 else openai_key}")
    else:
        print("❌ OPENAI_API_KEY not found in environment")
    
    # Check other common variables
    common_vars = ['DJANGO_SETTINGS_MODULE', 'DATABASE_URL', 'REDIS_URL', 'DEBUG']
    
    print(f"\n📋 Other environment variables:")
    for var in common_vars:
        value = os.getenv(var)
        if value:
            display_value = value[:30] + '...' if len(value) > 30 else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")

def check_python_dotenv():
    """Check if python-dotenv is installed and working"""
    print("\n🔍 CHECKING PYTHON-DOTENV")
    print("=" * 50)
    
    try:
        import dotenv
        print(f"✅ python-dotenv installed (version: {dotenv.__version__})")
        
        # Try to load .env manually
        env_files = check_env_file_locations()
        
        if env_files:
            for env_file in env_files:
                print(f"\n🧪 Testing manual load of {env_file}:")
                try:
                    # Store original value
                    original_value = os.getenv('OPENAI_API_KEY')
                    
                    # Load .env file
                    dotenv.load_dotenv(env_file)
                    
                    # Check if it worked
                    new_value = os.getenv('OPENAI_API_KEY')
                    if new_value and new_value != original_value:
                        print(f"   ✅ Successfully loaded OPENAI_API_KEY from {env_file}")
                        print(f"   Value: {new_value[:10]}...{new_value[-4:] if len(new_value) > 14 else new_value}")
                    elif new_value:
                        print(f"   ⚠️  OPENAI_API_KEY was already set (not from .env)")
                    else:
                        print(f"   ❌ Failed to load OPENAI_API_KEY from {env_file}")
                        
                except Exception as e:
                    print(f"   ❌ Error loading {env_file}: {e}")
        
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Install with: pip install python-dotenv")

def check_django_environ():
    """Check if django-environ is installed"""
    print("\n🔍 CHECKING DJANGO-ENVIRON")
    print("=" * 50)
    
    try:
        import environ
        print(f"✅ django-environ installed")
        
        # Test django-environ loading
        env = environ.Env()
        
        # Find .env file
        env_files = [
            Path('/Users/gabrielgomez/Personal/afp-project/.env'),
            Path('/Users/gabrielgomez/Personal/afp-project/backend/.env'),
        ]
        
        for env_file in env_files:
            if env_file.exists():
                print(f"🧪 Testing django-environ with {env_file}")
                try:
                    environ.Env.read_env(env_file)
                    key = env('OPENAI_API_KEY', default=None)
                    if key:
                        print(f"   ✅ django-environ loaded OPENAI_API_KEY")
                        print(f"   Value: {key[:10]}...{key[-4:] if len(key) > 14 else key}")
                    else:
                        print(f"   ❌ django-environ did not find OPENAI_API_KEY")
                except Exception as e:
                    print(f"   ❌ Error with django-environ: {e}")
                break
                
    except ImportError:
        print("❌ django-environ not installed")
        print("   Install with: pip install django-environ")

def check_django_settings():
    """Check Django settings configuration"""
    print("\n🔍 CHECKING DJANGO SETTINGS")
    print("=" * 50)
    
    try:
        # Add Django path
        sys.path.append('/Users/gabrielgomez/Personal/afp-project/backend')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        print("✅ Django settings loaded successfully")
        
        # Check if settings has environment loading logic
        settings_file = Path('/Users/gabrielgomez/Personal/afp-project/backend/afp_backend/settings.py')
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                content = f.read()
                
                if 'python-dotenv' in content or 'load_dotenv' in content:
                    print("✅ Found python-dotenv loading in settings.py")
                elif 'django-environ' in content or 'environ.Env' in content:
                    print("✅ Found django-environ usage in settings.py")
                else:
                    print("❌ No environment variable loading found in settings.py")
                    print("   This might be the problem!")
        
        # Try to access OPENAI_API_KEY through Django
        try:
            openai_key = getattr(settings, 'OPENAI_API_KEY', None)
            if openai_key:
                print(f"✅ OPENAI_API_KEY found in Django settings")
            else:
                print("❌ OPENAI_API_KEY not found in Django settings")
        except:
            print("❌ Error accessing OPENAI_API_KEY from Django settings")
            
    except Exception as e:
        print(f"❌ Error loading Django: {e}")

def provide_solutions():
    """Provide step-by-step solutions"""
    print("\n🔧 SOLUTIONS TO TRY")
    print("=" * 50)
    
    print("1️⃣ **Create/Update .env file in project root:**")
    print("   cd /Users/gabrielgomez/Personal/afp-project")
    print("   echo 'OPENAI_API_KEY=your-actual-api-key-here' > .env")
    print("   # Make sure there are NO spaces around the = sign!")
    print()
    
    print("2️⃣ **Install python-dotenv if not installed:**")
    print("   cd backend")
    print("   pip install python-dotenv")
    print()
    
    print("3️⃣ **Update Django settings.py to load .env:**")
    print("   Add at the top of afp_backend/settings.py:")
    print("   ```python")
    print("   from dotenv import load_dotenv")
    print("   import os")
    print("   from pathlib import Path")
    print()
    print("   # Load .env file")
    print("   load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')")
    print("   ```")
    print()
    
    print("4️⃣ **Alternative: Set environment variable directly:**")
    print("   export OPENAI_API_KEY='your-actual-api-key-here'")
    print("   # Add to ~/.zshrc or ~/.bashrc to make permanent")
    print()
    
    print("5️⃣ **Test the fix:**")
    print("   python backend/scripts/diagnose_env_variables.py")

def main():
    """Main diagnostic function"""
    print("🩺 ENVIRONMENT VARIABLE DIAGNOSTIC TOOL")
    print("=" * 60)
    
    check_env_file_locations()
    check_environment_variables()
    check_python_dotenv()
    check_django_environ()
    check_django_settings()
    provide_solutions()
    
    print("\n✅ Diagnostic complete!")
    print("Run the solutions above and test again.")

if __name__ == "__main__":
    main() 