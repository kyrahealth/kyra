#!/usr/bin/env python3
"""
Runner script for Cancer Research UK indexing
Provides a simple interface to run the indexing process with progress tracking.
"""

import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def main():
    """Run the Cancer Research UK indexing process."""
    print("🏥 Cancer Research UK Indexing Tool")
    print("=" * 50)
    
    try:
        # Import and run the advanced indexer
        from advanced_cancer_indexer import main as run_indexing
        
        start_time = time.time()
        run_indexing()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n✅ Indexing completed in {duration:.1f} seconds")
        
    except KeyboardInterrupt:
        print("\n⚠️  Indexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during indexing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 