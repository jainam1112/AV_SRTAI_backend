#!/usr/bin/env python3
"""
Enhanced upload endpoint with strict validation mode
"""

from fastapi import HTTPException
from validation_utils import validate_chunk_coverage, print_validation_summary

def upload_transcript_with_strict_validation(
    subtitles, processed_chunks, validation_mode="warn"
):
    """
    Enhanced validation with different modes:
    - "warn": Continue with warnings (default)
    - "strict": Fail if validation doesn't pass
    - "detailed": Include detailed validation in response
    """
    
    print("\n🔍 Running transcript validation...")
    validation_report = validate_chunk_coverage(subtitles, processed_chunks)
    print_validation_summary(validation_report)
    
    if validation_mode == "strict":
        if not validation_report["coverage_complete"]:
            error_details = {
                "validation_failed": True,
                "errors": validation_report["errors"],
                "warnings": validation_report["warnings"],
                "text_coverage": validation_report["text_coverage_percentage"],
                "timeline_coverage": validation_report["timeline_coverage_percentage"],
                "missing_subtitles": len(validation_report["missing_subtitles"]),
                "detailed_report": validation_report["detailed_report"]
            }
            
            raise HTTPException(
                status_code=422, 
                detail=f"Transcript validation failed: {validation_report['errors']}"
            )
    
    elif validation_mode == "warn":
        if not validation_report["coverage_complete"]:
            print("⚠️ Validation issues detected but continuing...")
            for error in validation_report["errors"]:
                print(f"   ❌ {error}")
            for warning in validation_report["warnings"]:
                print(f"   ⚠️ {warning}")
    
    return validation_report

# Example configurations for different validation modes:

# Configuration 1: Strict Mode (Recommended for production)
VALIDATION_CONFIG_STRICT = {
    "mode": "strict",
    "min_text_coverage": 98.0,
    "min_timeline_coverage": 98.0,
    "max_missing_subtitles": 0,
    "max_timeline_gaps": 0
}

# Configuration 2: Lenient Mode (For testing/development)
VALIDATION_CONFIG_LENIENT = {
    "mode": "warn", 
    "min_text_coverage": 90.0,
    "min_timeline_coverage": 90.0,
    "max_missing_subtitles": 2,
    "max_timeline_gaps": 3
}

# Configuration 3: Detailed Mode (For debugging)
VALIDATION_CONFIG_DEBUG = {
    "mode": "detailed",
    "min_text_coverage": 95.0,
    "min_timeline_coverage": 95.0,
    "save_validation_report": True,
    "include_in_response": True
}

def get_validation_config(mode="production"):
    """Get validation configuration based on environment"""
    
    configs = {
        "production": VALIDATION_CONFIG_STRICT,
        "development": VALIDATION_CONFIG_LENIENT,
        "testing": VALIDATION_CONFIG_LENIENT,
        "debug": VALIDATION_CONFIG_DEBUG
    }
    
    return configs.get(mode, VALIDATION_CONFIG_LENIENT)

if __name__ == "__main__":
    print("📋 Available Validation Configurations:")
    print("\n1. STRICT MODE (Production):")
    for key, value in VALIDATION_CONFIG_STRICT.items():
        print(f"   {key}: {value}")
    
    print("\n2. LENIENT MODE (Development):")
    for key, value in VALIDATION_CONFIG_LENIENT.items():
        print(f"   {key}: {value}")
    
    print("\n3. DEBUG MODE (Testing):")
    for key, value in VALIDATION_CONFIG_DEBUG.items():
        print(f"   {key}: {value}")
    
    print("\n💡 To use in main.py:")
    print('   config = get_validation_config("production")')
    print('   validation_report = upload_transcript_with_strict_validation(')
    print('       subtitles, processed_chunks, config["mode"])')
