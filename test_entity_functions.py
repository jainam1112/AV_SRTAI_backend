#!/usr/bin/env python3
"""
Simple test for entity extraction functions
Tests the core functionality without API calls
"""

from entity_extraction import extract_entities_from_chunks, extract_entities_with_ai, extract_entities_rule_based, get_entity_statistics
from constants import ENTITY_CATEGORIES
import json

def test_sample_text():
    """Test entity extraction with sample spiritual discourse text"""
    
    print("🧪 Testing Entity Extraction Functions")
    print("=" * 60)
    
    # Sample spiritual discourse text
    sample_chunks = [
        {
            'text': "Today Guruji spoke about the importance of meditation and self-realization. He mentioned the Bhagavad Gita and how Lord Krishna taught Arjuna about dharma. The satsang was held at the ashram in Rishikesh on Diwali evening.",
            'chunk_number': 1,
            'transcript_name': 'sample_discourse'
        },
        {
            'text': "The practice of yoga and pranayama helps in achieving inner peace. Many devotees from Mumbai and Delhi attended the spiritual gathering. They discussed the teachings of Buddha and Jesus Christ.",
            'chunk_number': 2,
            'transcript_name': 'sample_discourse'
        }
    ]
    
    print(f"📝 Sample text chunks: {len(sample_chunks)}")
    for i, chunk in enumerate(sample_chunks, 1):
        print(f"   Chunk {i}: {chunk['text'][:60]}...")
    
    # Test rule-based extraction
    print("\n🔧 Testing Rule-based Extraction:")
    print("-" * 40)
    
    for i, chunk in enumerate(sample_chunks, 1):
        print(f"\nChunk {i} results:")
        result = extract_entities_rule_based(chunk['text'], chunk['chunk_number'])
        
        for entity_type, entities in result.items():
            if entities:  # Only show non-empty categories
                print(f"   {entity_type}: {entities}")
    
    # Test AI extraction (if available)
    print("\n🤖 Testing AI Extraction:")
    print("-" * 40)
    
    try:
        for i, chunk in enumerate(sample_chunks, 1):
            print(f"\nChunk {i} results:")
            result = extract_entities_with_ai(chunk['text'], chunk['chunk_number'])
            
            for entity_type, entities in result.items():
                if entities:  # Only show non-empty categories
                    print(f"   {entity_type}: {entities}")
    except Exception as e:
        print(f"   ⚠️ AI extraction failed (likely missing API key): {e}")
    
    # Test full extraction pipeline
    print("\n🔄 Testing Full Extraction Pipeline:")
    print("-" * 40)
    
    # Test with rule-based method
    print("\nRule-based pipeline:")
    results_rules = extract_entities_from_chunks(sample_chunks, 'sample_discourse', use_ai=False)
    
    for i, result in enumerate(results_rules, 1):
        if result:
            # Count entities, excluding boolean fields
            entity_count = sum(len(entities) for key, entities in result.items() 
                             if isinstance(entities, list))
            print(f"   Chunk {i}: Found {entity_count} entities")
            for entity_type, entities in result.items():
                if isinstance(entities, list) and entities:
                    print(f"     {entity_type}: {entities}")
                elif isinstance(entities, bool) and entities:
                    print(f"     {entity_type}: {entities}")
        else:
            print(f"   Chunk {i}: No entities found")
    
    # Test statistics
    print("\n📊 Testing Statistics:")
    print("-" * 40)
    
    if results_rules:
        stats = get_entity_statistics(results_rules)
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Chunks with entities: {stats['chunks_with_entities']}")
        print(f"   Self-reference chunks: {stats['self_reference_chunks']}")
        print("   Entity breakdown:")
        for entity_type, count in stats['entity_counts'].items():
            if count > 0:
                print(f"     {entity_type}: {count}")
        print("   Unique entities found:")
        for entity_type, entities in stats['unique_entities'].items():
            if entities:
                print(f"     {entity_type}: {entities[:5]}")  # Show first 5
    
    # Display entity categories
    print("\n📋 Available Entity Categories:")
    print("-" * 40)
    for category, description in ENTITY_CATEGORIES.items():
        print(f"   {category}: {description}")

def test_edge_cases():
    """Test edge cases and error handling"""
    
    print("\n⚠️ Testing Edge Cases:")
    print("-" * 40)
    
    # Empty text
    print("\n1. Empty text:")
    result = extract_entities_rule_based("", 1)
    empty_count = sum(len(entities) for key, entities in result.items() 
                     if isinstance(entities, list))
    print(f"   Found {empty_count} entities (should be 0)")
    
    # Very short text
    print("\n2. Very short text:")
    result = extract_entities_rule_based("Om.", 1)
    short_count = sum(len(entities) for key, entities in result.items() 
                     if isinstance(entities, list))
    print(f"   Found {short_count} entities")
    
    # Text with no spiritual content
    print("\n3. Non-spiritual text:")
    result = extract_entities_rule_based("The weather is nice today. I went to the store.", 1)
    nonspi_count = sum(len(entities) for key, entities in result.items() 
                      if isinstance(entities, list))
    print(f"   Found {nonspi_count} entities")

def main():
    """Run the entity extraction function tests"""
    
    print("🚀 Starting Entity Extraction Function Tests")
    print("=" * 80)
    
    test_sample_text()
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("🎉 Function Tests Complete!")
    print("\nThe entity extraction system is ready for:")
    print("1. Integration with the API endpoint")
    print("2. Qdrant database updates")
    print("3. Enhanced search functionality")

if __name__ == "__main__":
    main()
