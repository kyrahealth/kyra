#!/usr/bin/env python3
"""
Test script for Cancer Research UK indexing
Verifies the indexing process and checks results.
"""

import sys
import time
from pathlib import Path
from chromadb import PersistentClient

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_indexing():
    """Test the Cancer Research UK indexing process."""
    print("🧪 Testing Cancer Research UK Indexing")
    print("=" * 50)
    
    try:
        # Import and run the advanced indexer
        from advanced_cancer_indexer import main as run_indexing
        
        print("🚀 Starting indexing process...")
        start_time = time.time()
        run_indexing()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n✅ Indexing completed in {duration:.1f} seconds")
        
        # Verify the results
        print("\n🔍 Verifying results...")
        verify_results()
        
    except KeyboardInterrupt:
        print("\n⚠️  Indexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during indexing: {e}")
        sys.exit(1)

def verify_results():
    """Verify that the indexing produced expected results."""
    try:
        # Check if the collections exist and have documents
        index_dir = Path(__file__).parent / "chroma_db"
        client = PersistentClient(path=str(index_dir))
        
        # Check NHS collection
        try:
            nhs_collection = client.get_collection("nhs_docs")
            nhs_count = nhs_collection.count()
            print(f"📊 NHS collection: {nhs_count} documents")
        except Exception as e:
            print(f"⚠️  NHS collection not found: {e}")
        
        # Check Cancer Research UK collection
        try:
            cancer_collection = client.get_collection("cancer_research_docs")
            cancer_count = cancer_collection.count()
            print(f"📊 Cancer Research UK collection: {cancer_count} documents")
        except Exception as e:
            print(f"⚠️  Cancer Research UK collection not found: {e}")
        
        # Check processing stats
        stats_file = Path(__file__).parent / "processing_stats.json"
        if stats_file.exists():
            import json
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            print(f"📈 Processing statistics:")
            print(f"   - Total URLs found: {stats.get('total_urls_found', 0)}")
            print(f"   - Relevant URLs found: {stats.get('relevant_urls_found', 0)}")
            print(f"   - Successfully processed: {stats.get('successfully_processed', 0)}")
            print(f"   - Failed URLs: {len(stats.get('failed_urls', []))}")
            print(f"   - Final embedded count: {stats.get('final_embedded_count', 0)}")
        
        print("\n✅ Verification completed!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

def test_rag_integration():
    """Test that the RAG service can use the new Cancer Research UK data."""
    print("\n🔍 Testing RAG integration...")
    
    try:
        # Import the RAG service
        sys.path.append(str(Path(__file__).parent.parent / "app" / "services"))
        from rag import get_rag_context_weighted
        
        # Test queries
        test_queries = [
            "What are the symptoms of breast cancer?",
            "How is cancer diagnosed?",
            "What are the treatment options for lung cancer?",
            "Tell me about cancer screening",
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: {query}")
            context, score, sources = get_rag_context_weighted(query)
            
            if context:
                print(f"✅ Found context (score: {score:.3f})")
                print(f"📚 Sources: {len(sources)} found")
                for source in sources[:3]:  # Show first 3 sources
                    print(f"   - {source}")
            else:
                print(f"❌ No relevant context found (score: {score:.3f})")
        
        print("\n✅ RAG integration test completed!")
        
    except Exception as e:
        print(f"❌ Error during RAG integration test: {e}")

if __name__ == "__main__":
    # Run the indexing test
    test_indexing()
    
    # Run the RAG integration test
    test_rag_integration() 