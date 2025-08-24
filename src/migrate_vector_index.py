#!/usr/bin/env python3
"""
Migration script to create initial FAISS vector index from existing notes
Run this once to build the initial search index for semantic search functionality
"""

import sys
import os
from pathlib import Path

# Add src directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

from utils import *

def check_notes_exist():
    """Check if there are any notes in the database"""
    try:
        with DBConn() as _conn:
            sql_stmt = f"""
                SELECT COUNT(*) as count 
                FROM {CFG['TABLE_NOTE']} 
                WHERE is_active = 1
            """
            df = pd.read_sql(sql_stmt, _conn)
            return df.iloc[0]['count'] > 0
    except Exception as e:
        print(f"Error checking notes: {e}")
        return False

def main():
    print("🚀 Starting FAISS vector index migration...")
    
    # Check if notes exist
    if not check_notes_exist():
        print("ℹ️  No active notes found in database. Nothing to migrate.")
        return
    
    # Get all available embedding models
    available_models = list(CFG["EMBEDDING_MODELS"].keys())
    print(f"📊 Building indexes for all embedding models: {', '.join(available_models)}")
    
    # Check if any indexes already exist
    existing_indexes = []
    for model_name in available_models:
        index_path = get_index_path(model_name)
        if os.path.exists(index_path):
            existing_indexes.append((model_name, index_path))
    
    if existing_indexes:
        print(f"⚠️  Found existing indexes:")
        for model_name, index_path in existing_indexes:
            print(f"   - {model_name}: {index_path}")
        response = input("Rebuild all existing indexes? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled.")
            return
    
    try:
        successful_builds = 0
        total_models = len(available_models)
        
        for i, model_name in enumerate(available_models, 1):
            print(f"\n📊 [{i}/{total_models}] Building FAISS index using model: {model_name}")
            
            # Use the existing build_faiss_index function
            index, note_ids = build_faiss_index(model_name)
            
            if index is None:
                print(f"   ⚠️  No notes to process for {model_name}")
                continue
            
            index_path = get_index_path(model_name)
            print(f"   ✅ Index built successfully for {model_name}")
            print(f"      📊 Processed {len(note_ids)} notes")
            print(f"      📁 Index saved to {index_path}")
            print(f"      🎯 Index dimension: {index.d}")
            
            successful_builds += 1
        
        print(f"\n🎉 Migration completed!")
        print(f"   ✅ Successfully built {successful_builds}/{total_models} indexes")
        
        # Test search functionality with default model
        if successful_builds > 0:
            print("🧪 Testing search functionality...")
            test_results = semantic_search("test query", top_k=3)
            print(f"   ✅ Search test passed: found {len(test_results)} results")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()