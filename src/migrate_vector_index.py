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
    
    # Check if index already exists
    if os.path.exists(CFG["FAISS_INDEX_PATH"]):
        response = input(f"⚠️  FAISS index already exists at {CFG['FAISS_INDEX_PATH']}. Rebuild? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled.")
            return
    
    try:
        print("📊 Loading embedding model...")
        model = load_embedding_model()
        print(f"✅ Model loaded: {CFG['EMBEDDING_MODEL']}")
        
        print("📝 Fetching notes from database...")
        with DBConn() as _conn:
            sql_stmt = f"""
                SELECT id, note_name, note, url, tags 
                FROM {CFG['TABLE_NOTE']} 
                WHERE is_active = 1
                ORDER BY id
            """
            df = pd.read_sql(sql_stmt, _conn)
        
        print(f"📋 Found {len(df)} notes to process")
        
        if df.empty:
            print("ℹ️  No notes to process.")
            return
        
        print("🔄 Building embeddings...")
        texts = []
        note_ids = []
        
        for i, row in df.iterrows():
            combined_text = combine_note_text(
                row['note_name'], row['note'], row['url'], row['tags']
            )
            texts.append(combined_text)
            note_ids.append(row['id'])
            
            if (i + 1) % 10 == 0:
                print(f"   Processed {i + 1}/{len(df)} notes...")
        
        print("🧠 Generating embeddings...")
        embeddings = model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
        
        print("🔧 Building FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))
        
        # Ensure db directory exists
        os.makedirs(os.path.dirname(CFG["FAISS_INDEX_PATH"]), exist_ok=True)
        
        print(f"💾 Saving index to {CFG['FAISS_INDEX_PATH']}...")
        faiss.write_index(index, CFG["FAISS_INDEX_PATH"])
        
        print(f"✅ Migration completed successfully!")
        print(f"   📊 Processed {len(df)} notes")
        print(f"   🧠 Generated {len(embeddings)} embeddings")
        print(f"   📁 Index saved to {CFG['FAISS_INDEX_PATH']}")
        print(f"   🎯 Index dimension: {dimension}")
        
        # Test the index
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