#!/usr/bin/env python3
"""
Helper script to configure your fine-tuned model
"""

import os
from dotenv import load_dotenv

def check_model_configuration():
    """Check current model configuration"""
    load_dotenv()
    
    print("=== Current Model Configuration ===\n")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    ft_model = os.getenv("FINE_TUNED_BIO_MODEL")
    default_model = os.getenv("ANSWER_EXTRACTION_MODEL")
    
    print(f"OpenAI API Key: {'✓ Set' if openai_key else '✗ Missing'}")
    print(f"Fine-tuned Bio Model: {ft_model if ft_model else '✗ Not set'}")
    print(f"Default Extraction Model: {default_model if default_model else '✗ Not set'}")
    
    print("\n=== Instructions ===\n")
    
    if ft_model and ft_model != "your_fine_tuned_model_id_here":
        print("✓ Fine-tuned model is configured!")
        print(f"  Model ID: {ft_model}")
        print("  The bio extraction will use this model by default.")
    else:
        print("⚠️  Fine-tuned model not configured.")
        print("   Please update your .env file:")
        print("   FINE_TUNED_BIO_MODEL=ft:gpt-3.5-turbo:your-org:your-model:id")
        print("\n   To find your fine-tuned model ID:")
        print("   1. Go to OpenAI Platform (platform.openai.com)")
        print("   2. Navigate to 'Fine-tuning' section")
        print("   3. Find your trained model")
        print("   4. Copy the model ID (format: ft:gpt-3.5-turbo:org:name:id)")
    
    print("\n=== Testing ===\n")
    print("Run this command to test biographical extraction:")
    print("   python test_bio_extraction.py")

def update_env_with_model_id():
    """Interactive function to help update .env file"""
    print("=== Update Fine-tuned Model ID ===\n")
    
    model_id = input("Enter your fine-tuned model ID (or press Enter to skip): ").strip()
    
    if not model_id:
        print("Skipped model ID update.")
        return
    
    if not model_id.startswith("ft:"):
        print("⚠️  Warning: Fine-tuned model IDs typically start with 'ft:'")
        print("   Example: ft:gpt-3.5-turbo:your-org:your-model:id")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return
    
    try:
        # Read current .env file
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update or add the fine-tuned model line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('FINE_TUNED_BIO_MODEL='):
                lines[i] = f"FINE_TUNED_BIO_MODEL={model_id}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"FINE_TUNED_BIO_MODEL={model_id}\n")
        
        # Write back to .env file
        with open('.env', 'w') as f:
            f.writelines(lines)
        
        print(f"✓ Updated .env file with model ID: {model_id}")
        print("  You can now run the bio extraction tests.")
        
    except Exception as e:
        print(f"✗ Error updating .env file: {e}")
        print("  Please manually update your .env file:")
        print(f"  FINE_TUNED_BIO_MODEL={model_id}")

if __name__ == "__main__":
    check_model_configuration()
    
    print("\n" + "="*50 + "\n")
    
    update_choice = input("Would you like to update your fine-tuned model ID now? (y/N): ").strip().lower()
    if update_choice == 'y':
        update_env_with_model_id()
    else:
        print("You can manually update the FINE_TUNED_BIO_MODEL in your .env file later.")
