#!/usr/bin/env python3
"""
Validation utilities for transcript chunk processing
"""

import re
from typing import List, Dict, Any, Tuple
from datetime import timedelta

def parse_timestamp(timestamp: str) -> float:
    """
    Convert SRT timestamp to seconds for comparison
    Handles formats like: 0:00:01.000, 00:00:01,000, 0:00:01
    """
    # Clean up the timestamp - remove commas, normalize format
    timestamp = timestamp.replace(',', '.')
    
    # Handle different formats
    if timestamp.count(':') == 2:  # H:MM:SS.mmm
        parts = timestamp.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + microseconds / 1000.0
    elif timestamp.count(':') == 1:  # M:SS.mmm
        parts = timestamp.split(':')
        minutes = int(parts[0])
        seconds_parts = parts[1].split('.')
        seconds = int(seconds_parts[0])
        microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        total_seconds = minutes * 60 + seconds + microseconds / 1000.0
    else:
        # Fallback - assume seconds only
        total_seconds = float(timestamp)
    
    return total_seconds

def validate_chunk_coverage(original_subtitles: List[Dict], processed_chunks: List[Dict]) -> Dict[str, Any]:
    """
    Comprehensive validation to ensure all subtitles are covered in chunks
    
    Returns validation report with:
    - coverage_complete: bool
    - missing_subtitles: List[Dict]
    - overlapping_chunks: List[Dict]
    - gaps_in_timeline: List[Dict]
    - text_coverage_percentage: float
    - detailed_report: str
    """
    
    validation_report = {
        "coverage_complete": False,
        "missing_subtitles": [],
        "overlapping_chunks": [],
        "gaps_in_timeline": [],
        "duplicate_content": [],
        "text_coverage_percentage": 0.0,
        "timeline_coverage_percentage": 0.0,
        "detailed_report": "",
        "warnings": [],
        "errors": []
    }
    
    if not original_subtitles:
        validation_report["errors"].append("No original subtitles provided")
        return validation_report
    
    if not processed_chunks:
        validation_report["errors"].append("No processed chunks provided")
        validation_report["detailed_report"] = "❌ No chunks were generated from the transcript"
        return validation_report
    
    # 1. Timeline Coverage Analysis
    print("🔍 Analyzing timeline coverage...")
    
    # Parse all timestamps
    subtitle_timeline = []
    for i, subtitle in enumerate(original_subtitles):
        start_time = parse_timestamp(subtitle["start"])
        end_time = parse_timestamp(subtitle["end"])
        subtitle_timeline.append({
            "index": i,
            "start": start_time,
            "end": end_time,
            "text": subtitle["text"],
            "covered": False
        })
    
    chunk_timeline = []
    for i, chunk in enumerate(processed_chunks):
        start_time = parse_timestamp(chunk["start"])
        end_time = parse_timestamp(chunk["end"])
        chunk_timeline.append({
            "index": i,
            "start": start_time,
            "end": end_time,
            "text": chunk["text"]
        })
    
    # Sort by start time
    subtitle_timeline.sort(key=lambda x: x["start"])
    chunk_timeline.sort(key=lambda x: x["start"])
    
    # Check timeline coverage
    total_subtitle_duration = subtitle_timeline[-1]["end"] - subtitle_timeline[0]["start"]
    covered_duration = 0
    
    for chunk in chunk_timeline:
        chunk_start = chunk["start"]
        chunk_end = chunk["end"]
        
        # Find overlapping subtitles
        for subtitle in subtitle_timeline:
            # Check if subtitle overlaps with chunk
            if (subtitle["start"] < chunk_end and subtitle["end"] > chunk_start):
                subtitle["covered"] = True
                # Calculate overlapping duration
                overlap_start = max(subtitle["start"], chunk_start)
                overlap_end = min(subtitle["end"], chunk_end)
                if overlap_end > overlap_start:
                    covered_duration += (overlap_end - overlap_start)
    
    validation_report["timeline_coverage_percentage"] = (covered_duration / total_subtitle_duration) * 100
    
    # 2. Text Coverage Analysis
    print("📝 Analyzing text coverage...")
    
    # Normalize text for comparison (remove extra whitespace, newlines)
    def normalize_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text.strip().lower())
    
    # Combine all original text
    original_text_combined = ' '.join([normalize_text(sub["text"]) for sub in original_subtitles])
    chunk_text_combined = ' '.join([normalize_text(chunk["text"]) for chunk in processed_chunks])
    
    # Calculate text coverage
    original_words = set(original_text_combined.split())
    chunk_words = set(chunk_text_combined.split())
    
    if original_words:
        text_coverage = len(chunk_words.intersection(original_words)) / len(original_words)
        validation_report["text_coverage_percentage"] = text_coverage * 100
    
    # 3. Find missing subtitles
    missing_subtitles = [sub for sub in subtitle_timeline if not sub["covered"]]
    validation_report["missing_subtitles"] = missing_subtitles
    
    # 4. Find gaps in timeline
    gaps = []
    for i in range(len(chunk_timeline) - 1):
        current_end = chunk_timeline[i]["end"]
        next_start = chunk_timeline[i + 1]["start"]
        
        if next_start > current_end + 1:  # Gap of more than 1 second
            gaps.append({
                "gap_start": current_end,
                "gap_end": next_start,
                "duration": next_start - current_end,
                "after_chunk": i,
                "before_chunk": i + 1
            })
    
    validation_report["gaps_in_timeline"] = gaps
    
    # 5. Find overlapping chunks
    overlaps = []
    for i in range(len(chunk_timeline) - 1):
        current_end = chunk_timeline[i]["end"]
        next_start = chunk_timeline[i + 1]["start"]
        
        if next_start < current_end:  # Overlap
            overlaps.append({
                "chunk1": i,
                "chunk2": i + 1,
                "overlap_duration": current_end - next_start,
                "overlap_start": next_start,
                "overlap_end": current_end
            })
    
    validation_report["overlapping_chunks"] = overlaps
    
    # 6. Check for duplicate content
    chunk_texts = [normalize_text(chunk["text"]) for chunk in processed_chunks]
    duplicates = []
    for i, text1 in enumerate(chunk_texts):
        for j, text2 in enumerate(chunk_texts[i+1:], i+1):
            # Check for significant overlap (>50% of words)
            words1 = set(text1.split())
            words2 = set(text2.split())
            if words1 and words2:
                overlap_ratio = len(words1.intersection(words2)) / len(words1.union(words2))
                if overlap_ratio > 0.5:
                    duplicates.append({
                        "chunk1": i,
                        "chunk2": j,
                        "overlap_ratio": overlap_ratio
                    })
    
    validation_report["duplicate_content"] = duplicates
    
    # 7. Generate warnings and errors
    if missing_subtitles:
        validation_report["errors"].append(f"Missing {len(missing_subtitles)} subtitles in chunks")
    
    if gaps:
        validation_report["warnings"].append(f"Found {len(gaps)} timeline gaps")
    
    if overlaps:
        validation_report["warnings"].append(f"Found {len(overlaps)} overlapping chunks")
    
    if duplicates:
        validation_report["warnings"].append(f"Found {len(duplicates)} duplicate content sections")
    
    if validation_report["text_coverage_percentage"] < 95:
        validation_report["errors"].append(f"Text coverage is only {validation_report['text_coverage_percentage']:.1f}%")
    
    if validation_report["timeline_coverage_percentage"] < 95:
        validation_report["errors"].append(f"Timeline coverage is only {validation_report['timeline_coverage_percentage']:.1f}%")
    
    # 8. Determine if coverage is complete
    validation_report["coverage_complete"] = (
        len(missing_subtitles) == 0 and
        validation_report["text_coverage_percentage"] >= 95 and
        validation_report["timeline_coverage_percentage"] >= 95 and
        len(validation_report["errors"]) == 0
    )
    
    # 9. Generate detailed report
    report_lines = []
    report_lines.append("📊 TRANSCRIPT VALIDATION REPORT")
    report_lines.append("=" * 50)
    
    if validation_report["coverage_complete"]:
        report_lines.append("✅ VALIDATION PASSED - All subtitles covered")
    else:
        report_lines.append("❌ VALIDATION FAILED - Issues detected")
    
    report_lines.append(f"\n📈 Coverage Statistics:")
    report_lines.append(f"   Text Coverage: {validation_report['text_coverage_percentage']:.1f}%")
    report_lines.append(f"   Timeline Coverage: {validation_report['timeline_coverage_percentage']:.1f}%")
    report_lines.append(f"   Original Subtitles: {len(original_subtitles)}")
    report_lines.append(f"   Generated Chunks: {len(processed_chunks)}")
    
    if validation_report["errors"]:
        report_lines.append(f"\n❌ ERRORS ({len(validation_report['errors'])}):")
        for error in validation_report["errors"]:
            report_lines.append(f"   • {error}")
    
    if validation_report["warnings"]:
        report_lines.append(f"\n⚠️ WARNINGS ({len(validation_report['warnings'])}):")
        for warning in validation_report["warnings"]:
            report_lines.append(f"   • {warning}")
    
    if missing_subtitles:
        report_lines.append(f"\n🚫 MISSING SUBTITLES ({len(missing_subtitles)}):")
        for sub in missing_subtitles[:5]:  # Show first 5
            report_lines.append(f"   • {sub['start']} - {sub['end']}: {sub['text'][:50]}...")
        if len(missing_subtitles) > 5:
            report_lines.append(f"   ... and {len(missing_subtitles) - 5} more")
    
    if gaps:
        report_lines.append(f"\n⏳ TIMELINE GAPS ({len(gaps)}):")
        for gap in gaps:
            report_lines.append(f"   • Gap: {gap['gap_start']:.1f}s - {gap['gap_end']:.1f}s (duration: {gap['duration']:.1f}s)")
    
    if overlaps:
        report_lines.append(f"\n🔄 OVERLAPPING CHUNKS ({len(overlaps)}):")
        for overlap in overlaps:
            report_lines.append(f"   • Chunks {overlap['chunk1']} & {overlap['chunk2']}: {overlap['overlap_duration']:.1f}s overlap")
    
    if duplicates:
        report_lines.append(f"\n📋 DUPLICATE CONTENT ({len(duplicates)}):")
        for dup in duplicates:
            report_lines.append(f"   • Chunks {dup['chunk1']} & {dup['chunk2']}: {dup['overlap_ratio']:.1%} similarity")
    
    validation_report["detailed_report"] = "\n".join(report_lines)
    
    return validation_report

def print_validation_summary(validation_report: Dict[str, Any]):
    """Print a concise validation summary"""
    print("\n" + "="*50)
    print("📊 VALIDATION SUMMARY")
    print("="*50)
    
    if validation_report["coverage_complete"]:
        print("✅ Status: PASSED")
    else:
        print("❌ Status: FAILED")
    
    print(f"📝 Text Coverage: {validation_report['text_coverage_percentage']:.1f}%")
    print(f"⏱️ Timeline Coverage: {validation_report['timeline_coverage_percentage']:.1f}%")
    print(f"🚫 Missing Subtitles: {len(validation_report['missing_subtitles'])}")
    print(f"❌ Errors: {len(validation_report['errors'])}")
    print(f"⚠️ Warnings: {len(validation_report['warnings'])}")
    
    if validation_report["errors"]:
        print("\n❌ Critical Issues:")
        for error in validation_report["errors"]:
            print(f"   • {error}")
    
    print("="*50)
