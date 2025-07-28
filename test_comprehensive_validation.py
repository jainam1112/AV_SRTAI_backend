#!/usr/bin/env python3
"""
Comprehensive test of validation system with real transcript
"""

import json
from srt_processor import parse_srt
from main import process_transcript_with_llm
from validation_utils import validate_chunk_coverage, print_validation_summary

def test_full_validation():
    """Test the complete validation pipeline"""
    
    print("🧪 COMPREHENSIVE VALIDATION TEST")
    print("="*50)
    
    # Step 1: Load and parse SRT
    print("\n1️⃣ Loading test SRT file...")
    with open("debug_test.srt", "r", encoding="utf-8") as f:
        srt_content = f.read()
    
    chunks = parse_srt(srt_content)
    print(f"✅ Parsed {len(chunks)} original subtitles from SRT")
    
    # Step 2: Prepare subtitles for LLM
    subtitles = [
        {"start": c["start"], "end": c["end"], "text": c["text"]}
        for c in chunks
    ]
    
    print(f"📝 Prepared {len(subtitles)} subtitles for processing")
    
    # Step 3: Process with LLM
    print("\n2️⃣ Processing with LLM...")
    with open("transcript_processing_prompt", "r", encoding="utf-8") as f:
        prompt = f.read()
    
    llm_result = process_transcript_with_llm(subtitles, prompt)
    processed_chunks = llm_result.get("chunks", [])
    
    print(f"✅ LLM generated {len(processed_chunks)} chunks")
    
    # Step 4: Comprehensive validation
    print("\n3️⃣ Running comprehensive validation...")
    validation_report = validate_chunk_coverage(subtitles, processed_chunks)
    
    # Step 5: Display results
    print("\n4️⃣ Validation Results:")
    print_validation_summary(validation_report)
    
    # Step 6: Detailed analysis
    print("\n5️⃣ Detailed Validation Report:")
    print(validation_report["detailed_report"])
    
    # Step 7: Save comprehensive report
    report_data = {
        "test_info": {
            "test_file": "debug_test.srt",
            "original_subtitles_count": len(subtitles),
            "processed_chunks_count": len(processed_chunks),
            "test_timestamp": "2025-07-27T17:50:00"
        },
        "original_subtitles": subtitles,
        "processed_chunks": processed_chunks,
        "validation_report": validation_report
    }
    
    with open("validation_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed report saved to: validation_test_report.json")
    
    # Step 8: Actionable recommendations
    print("\n6️⃣ Actionable Recommendations:")
    
    if validation_report["coverage_complete"]:
        print("✅ Validation PASSED - No action required")
        print("   • All subtitles are properly covered in chunks")
        print("   • Text and timeline coverage is complete")
    else:
        print("❌ Validation FAILED - Action required:")
        
        if validation_report["missing_subtitles"]:
            print(f"   🚫 Fix {len(validation_report['missing_subtitles'])} missing subtitles")
            print("      → Check LLM prompt to ensure it includes all subtitle text")
            print("      → Verify LLM response parsing is working correctly")
        
        if validation_report["gaps_in_timeline"]:
            print(f"   ⏳ Fix {len(validation_report['gaps_in_timeline'])} timeline gaps")
            print("      → Ensure chunks cover the entire transcript timeline")
        
        if validation_report["text_coverage_percentage"] < 95:
            print(f"   📝 Improve text coverage from {validation_report['text_coverage_percentage']:.1f}% to 95%+")
            print("      → Check if LLM is dropping or modifying original text")
    
    print("\n✅ Validation test complete!")
    return validation_report

if __name__ == "__main__":
    test_full_validation()
