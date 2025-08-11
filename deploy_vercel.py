#!/usr/bin/env python3
"""
Vercel Deployment Helper Script
Prepares the FastAPI backend for Vercel deployment
"""

import os
import sys
import json
import subprocess

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'main.py',
        'requirements.txt',
        'vercel.json',
        'api/index.py',
        'runtime.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files are present")
    return True

def check_environment_variables():
    """Check if environment variables are set"""
    required_env_vars = [
        'OPENAI_API_KEY',
        'QDRANT_URL', 
        'QDRANT_API_KEY',
        'ANSWER_EXTRACTION_MODEL'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️ Missing environment variables (set these in Vercel dashboard):")
        for var in missing_vars:
            print(f"   - {var}")
    else:
        print("✅ All environment variables are available locally")
    
    return len(missing_vars) == 0

def test_imports():
    """Test if all imports work"""
    try:
        # Test main imports
        print("🧪 Testing imports...")
        
        # Check if main modules can be imported
        import main
        print("✅ main.py imports successfully")
        
        import entity_extraction
        print("✅ entity_extraction.py imports successfully")
        
        import bio_extraction
        print("✅ bio_extraction.py imports successfully")
        
        import quadrant_client
        print("✅ quadrant_client.py imports successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing imports: {e}")
        return False

def create_git_commands():
    """Generate git commands for deployment"""
    commands = [
        "# Git commands for deployment",
        "git add .",
        "git commit -m 'Prepare for Vercel deployment'",
        "git push origin main"
    ]
    
    print("\n📝 Git commands to run:")
    for cmd in commands:
        print(f"   {cmd}")

def create_vercel_commands():
    """Generate Vercel CLI commands"""
    commands = [
        "# Vercel deployment commands",
        "npm install -g vercel",
        "vercel login",
        "vercel --prod"
    ]
    
    print("\n🚀 Vercel deployment commands:")
    for cmd in commands:
        print(f"   {cmd}")

def main():
    """Main deployment preparation function"""
    print("🔧 Vercel Deployment Preparation")
    print("=" * 50)
    
    # Check current directory
    if not os.path.exists('main.py'):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Run checks
    files_ok = check_requirements()
    env_ok = check_environment_variables()
    imports_ok = test_imports()
    
    print("\n" + "=" * 50)
    print("📋 Deployment Readiness Summary")
    print("=" * 50)
    
    if files_ok and imports_ok:
        print("✅ Your application is ready for Vercel deployment!")
        
        print("\n📋 Next Steps:")
        print("1. Push your code to GitHub")
        print("2. Set up environment variables in Vercel dashboard")
        print("3. Deploy using Vercel CLI or dashboard")
        
        create_git_commands()
        create_vercel_commands()
        
        print("\n🔗 Important Links:")
        print("   - Vercel Dashboard: https://vercel.com/dashboard")
        print("   - Deployment Guide: ./VERCEL_DEPLOYMENT_GUIDE.md")
        print("   - GitHub: https://github.com")
        
    else:
        print("❌ Please fix the issues above before deploying")
        
    if not env_ok:
        print("\n⚠️ Remember to set environment variables in Vercel dashboard:")
        print("   - OPENAI_API_KEY")
        print("   - QDRANT_URL")
        print("   - QDRANT_API_KEY") 
        print("   - ANSWER_EXTRACTION_MODEL")

if __name__ == "__main__":
    main()
