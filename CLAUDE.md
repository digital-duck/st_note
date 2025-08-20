# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

Smart Notes is an AI-powered note-taking application built with Streamlit that combines traditional keyword search with semantic search using FAISS vector store and sentence transformers. The app features a hybrid search system, intelligent tag parsing, and real-time search index updates.

## Core Development Commands

### Running the Application
```bash
# Start the app (from src/ directory)
cd src
streamlit run Welcome.py

# Alternative using the run script
cd src
bash 000_run_app.sh
```

### Database and Search Index Management
```bash
# Initialize/rebuild FAISS vector index from existing notes
cd src
python migrate_vector_index.py
```

### Dependencies
```bash
# Install all requirements
pip install -r requirements.txt

# Key dependencies: streamlit, pandas, sqlite3, sentence-transformers, faiss-cpu, streamlit-aggrid
```

## Architecture Overview

### Core Components
- **Frontend**: Streamlit web interface with multi-page structure
- **Database**: SQLite database (`src/db/notes.sqlite3`) with schema defined in `src/db/tables_ddl.sql`
- **Search Engine**: Dual system - SQL-based keyword search + FAISS vector search for semantic similarity
- **Vector Index**: Model-specific FAISS indexes stored as `src/db/notes_faiss_{model}.index`

### File Structure
```
src/
├── Welcome.py              # Main entry point and app configuration
├── pages/1-📝Notes.py     # Primary notes interface with search and CRUD
├── utils.py               # Core business logic, database operations, semantic search
├── ui_layout.py           # UI component definitions and form layouts  
├── migrate_vector_index.py # Initial vector index creation script
└── db/                    # Database files and schema
```

### Key Data Models

**t_note table** (`src/db/tables_ddl.sql:2`):
- Primary fields: `note_name`, `note`, `url/url2/url3`, `tags`, `note_type`
- System fields: `id`, `is_active`, `created_at/updated_at`, `created_by/updated_by`
- Note: `note_type` constraint removed - uses list-of-values validation in UI instead
- Supports up to 3 URL fields for multiple link references
- UI configuration defined in `COLUMN_PROPS` dict in `src/ui_layout.py:2`

### Search System Architecture

**Three Search Modes** (`src/pages/1-📝Notes.py:58`):
1. **Keyword**: Traditional SQL LIKE queries on text fields
2. **Semantic**: FAISS vector similarity search using sentence transformers  
3. **Hybrid**: Combines both with OR logic for comprehensive results

**Embedding Models** (`src/utils.py:90`):
- English (Fast): `all-MiniLM-L6-v2` - optimized for English content
- Multilingual (EN+CN): `paraphrase-multilingual-MiniLM-L12-v2` - supports Chinese and English

**Vector Index Management**:
- Auto-rebuilds on save/update/delete operations (`src/utils.py:956`)
- Manual refresh available in sidebar for troubleshooting
- Model-specific index files for different embedding models

### Tag System
- Multi-delimiter parsing (commas, spaces) with normalization (`src/pages/1-📝Notes.py:10`)
- Case-insensitive matching with uppercase storage
- Individual tag filtering via multiselect dropdown

## Development Workflow

### Adding New Features
1. **Database Changes**: Update `src/db/tables_ddl.sql` and column properties in `src/ui_layout.py`
2. **UI Changes**: Modify pages in `src/pages/` or UI components in `src/ui_layout.py`
3. **Form Field Tooltips**: Add `tooltip` attribute to field definitions in `COLUMN_PROPS` for help text
4. **Search Logic**: Extend semantic search functions in `src/utils.py` (lines 1217-1360)
5. **Configuration**: Update `CFG` dict in `src/utils.py:76` for new settings

### Database Operations
- All database operations go through `DBConn()` context manager (`src/utils.py:117`)
- Use `db_upsert()` for save operations with automatic timestamps (`src/utils.py:302`)
- Search index automatically refreshes after data changes (`src/utils.py:956`)

### Semantic Search Integration
- Vector embeddings generated via `combine_note_text()` (`src/utils.py:1239`)
- FAISS index operations in `build_faiss_index()` and `load_faiss_index()` (`src/utils.py:1254`)
- Search threshold and top-k configurable via sidebar (`src/pages/1-📝Notes.py:178`)

## Configuration

### Key Settings (`src/utils.py:76`)
- `EMBEDDING_MODELS`: Available sentence transformer models
- `DEFAULT_EMBEDDING_MODEL`: Default model selection
- `FAISS_INDEX_PATH`: Template for model-specific index file paths
- `TABLE_NOTE`: Main table name for notes

### UI Configuration (`src/ui_layout.py:2`)
- `COLUMN_PROPS`: Defines form layout, widget types, field properties, and tooltips
- Form columns organized as COL_1, COL_2, COL_3 with numbered sub-fields
- Widget types: text_input, text_area, selectbox for different field types
- Optional `tooltip` attribute provides help text on hover for form fields

## Important Implementation Notes

### Error Handling
- Graceful degradation: semantic search failures don't break keyword search
- Search index rebuild failures don't prevent note saving (`src/utils.py:958`)
- Database operations wrapped in try-catch with user feedback

### Performance Considerations
- FAISS index uses cosine similarity with L2 normalization
- Embedding model cached with `@st.cache_resource` decorator (`src/utils.py:1221`)
- Search results limited by configurable top_k parameter

### Multi-Language Support
- Multiple embedding models available for different language needs
- Model selection persisted in session state
- Index files are model-specific to prevent conflicts

### Data Import/Export
- **CSV Export**: Export search results with timestamps (`src/pages/1-📝Notes.py:200`)
- **CSV Import**: Bulk import notes with validation and duplicate handling (`src/pages/1-📝Notes.py:207`)
  - Required columns: `note_name`
  - Optional columns: `note`, `url`, `url2`, `url3`, `note_type`, `tags`, `is_active`
  - Duplicate detection: Uses composite key (`note_name` + `note_type`)
  - Options: Skip duplicates, Update existing notes
  - Auto-updates search index after import

This codebase emphasizes maintainable architecture with clear separation between UI, business logic, and data operations while providing sophisticated AI-powered search capabilities.