#!/usr/bin/env python3
"""
Debug script to investigate why no chunks are being created
"""

import json
import os
from dotenv import load_dotenv
import openai
from srt_processor import parse_srt

# Load environment variables
load_dotenv()

def debug_chunk_creation():
    print("🔍 Debugging chunk creation process...")
    
    # Step 1: Test SRT parsing
    print("\n1️⃣ Testing SRT parsing...")
    with open("debug_test.srt", "r", encoding="utf-8") as f:
        srt_content = f.read()
    
    print(f"SRT Content:\n{srt_content[:200]}...")
    
    chunks = parse_srt(srt_content)
    print(f"Parsed {len(chunks)} chunks from SRT")
    
    if chunks:
        print("First chunk:", chunks[0])
    else:
        print("❌ No chunks parsed from SRT!")
        return
    
    # Step 2: Prepare subtitles for LLM
    print("\n2️⃣ Preparing subtitles for LLM...")
    subtitles = [
        {"start": c["start"], "end": c["end"], "text": c["text"]}
        for c in chunks
    ]
    print(f"Prepared {len(subtitles)} subtitles")
    print("First subtitle:", subtitles[0])
    
    # Step 3: Load prompt
    print("\n3️⃣ Loading transcript processing prompt...")
    try:
        with open("transcript_processing_prompt", "r", encoding="utf-8") as f:
            prompt = f.read()
        print(f"Loaded prompt ({len(prompt)} characters)")
        print("Prompt preview:", prompt[:200] + "...")
    except FileNotFoundError:
        print("❌ transcript_processing_prompt file not found!")
        return
    
    # Step 4: Test LLM processing
    print("\n4️⃣ Testing LLM processing...")
    
    def test_process_transcript_with_llm(subtitles, prompt):
        input_json = json.dumps(subtitles, ensure_ascii=False)
        full_prompt = f"{prompt}\n\nINPUT:\n{input_json}\n\nOUTPUT:"
        
        print(f"Full prompt length: {len(full_prompt)} characters")
        print(f"OpenAI API Key set: {'OPENAI_API_KEY' in os.environ}")
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for transcript chunking."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.2,
                max_tokens=4096
            )
            
            output_text = response.choices[0].message.content.strip()
            print(f"LLM response length: {len(output_text)} characters")
            print(f"LLM response preview: {output_text[:500]}...")
            
            try:
                result = json.loads(output_text)
                print(f"✅ Successfully parsed JSON response")
                print(f"Keys in result: {list(result.keys())}")
                
                if 'chunks' in result:
                    print(f"Number of chunks in result: {len(result['chunks'])}")
                    if result['chunks']:
                        print("First chunk keys:", list(result['chunks'][0].keys()))
                    else:
                        print("❌ Chunks array is empty!")
                else:
                    print("❌ No 'chunks' key in result!")
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"Raw output: {output_text}")
                return {"raw_output": output_text, "chunks": []}
                
        except Exception as e:
            print(f"❌ LLM API call failed: {e}")
            return {"chunks": [], "error": str(e)}
    
    llm_result = test_process_transcript_with_llm(subtitles, prompt)
    
    # Step 5: Summary
    print("\n📊 SUMMARY:")
    print(f"SRT chunks parsed: {len(chunks)}")
    print(f"Subtitles prepared: {len(subtitles)}")
    print(f"LLM chunks returned: {len(llm_result.get('chunks', []))}")
    
    if 'error' in llm_result:
        print(f"❌ Error encountered: {llm_result['error']}")
    elif llm_result.get('chunks'):
        print("✅ Chunks successfully created!")
    else:
        print("❌ No chunks were created by LLM")
        if 'raw_output' in llm_result:
            print("Raw LLM output for inspection:")
            print(llm_result['raw_output'])

if __name__ == "__main__":
    debug_chunk_creation()
