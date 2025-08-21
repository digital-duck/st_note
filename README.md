# Smart Notes 📝

An AI-powered note-taking application that revolutionizes information management through semantic understanding and flexible content architecture.

## 🧠 AI-Native Data Philosophy

Smart Notes embraces a fundamentally different approach to data architecture—one that leverages AI's semantic understanding rather than rigid traditional schemas.

### Traditional vs. AI-Powered Approach

**Traditional Enterprise Software:**
- Rigid schemas, strict normalization, complex joins
- Predetermined relationships through foreign keys
- Schema migrations for business changes
- Data silos across domains

**Smart Notes AI-Native Design:**
- Flexible content with semantic understanding
- Natural relationships discovered through AI
- Content-first architecture
- Cross-domain intelligence

## 🎯 Trinity Framework: People, Product, Process

Our note classification system is built around three fundamental enterprise domains that cover virtually all business information:

### 👥 People Domain
- **Person**: Individual contacts, expertise, relationships
- **Organization**: Companies, teams, departments
- **Community**: Networks, groups, ecosystems

### 📦 Product Domain  
- **Application**: Software products, tools, platforms
- **Startup**: Ventures, business models, market analysis
- **Project**: Initiatives, deliverables, roadmaps

### ⚙️ Process Domain
- **Task**: Action items, workflows, procedures
- **Meeting**: Discussions, decisions, outcomes
- **Event**: Conferences, workshops, milestones
- **Learning**: Knowledge acquisition, research insights
- **Research**: Analysis, findings, documentation

## 🚀 Core Features

### Hybrid Search System
- **Keyword Search**: Traditional SQL-based text matching
- **Semantic Search**: AI-powered similarity using sentence transformers
- **Hybrid Mode**: Combines both approaches for comprehensive results

### Intelligent Content Understanding
- **Cross-Domain Discovery**: AI finds connections between people's expertise and product needs
- **Contextual Search**: Natural language queries like "Find all blockchain experts working on fintech projects"
- **Knowledge Emergence**: Patterns emerge from content, not predetermined structure

### Flexible Schema Evolution
- **No Schema Migrations**: Business changes don't require database restructuring
- **Natural Growth**: Add new note types and relationships organically
- **Unified Search**: All content remains searchable regardless of type

### Status Workflow Management
- **ToDo**: Items requiring action
- **WIP**: Work in progress  
- **Done**: Completed items
- **Blocked**: Items waiting on dependencies
- **Descoped**: Items removed from scope
- **Others**: Flexible catch-all status

## 🎥 Demo Video

*Coming soon! YouTube demo video will be available here.*

[![Demo Video Placeholder](https://img.shields.io/badge/Demo%20Video-Coming%20Soon-red?style=for-the-badge&logo=youtube)](https://youtube.com)

## 📸 Screenshots

### Main Interface - Semantic Search in Action
[![Smart Notes Interface](https://github.com/digital-duck/st_note/blob/main/docs/st_note_2.png)](https://github.com/digital-duck/st_note/blob/main/docs/st_note_2.png)



*Semantic search finding "workflow orchestration" matches across different notes - showcasing AI-powered contextual understanding*

### Search Modes
- **🔀 Hybrid**: Best of both keyword and semantic search
- **🧠 Semantic**: AI-powered contextual search  
- **📝 Keyword**: Traditional text matching

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/digital-duck/st_note.git
   cd st_note
   ```

2. **Create and activate virtual environment**
   ```bash
   conda create -n ai_workflow python=3.12
   conda activate ai_workflow 

   # or 
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database and vector index**
```bash
# Run the migration script to build initial FAISS index
cd src
python migrate_vector_index.py
```

5. **Launch the application**
```bash
cd src
streamlit run Welcome.py
```

6. **Access the app**
   - Open your browser to `http://localhost:8501`
   - Navigate to the "📝 Notes" page to start taking notes

## 📋 Usage Guide

### Adding Notes
1. Navigate to the "📝 Notes" page
2. Fill in the form with:
   - **Title**: Note name/title
   - **Description**: Note content
   - **URL/URL2/URL3**: Up to three optional related links
   - **Type**: Note category (learning, research, project, etc.)
   - **Tags**: Space or comma-separated tags
3. Click "✅ Save" - the search index updates automatically

### Searching Notes
1. **Type/Status/Tag Filter**: Select specific tags from the dropdown
2. **Search Mode**: Choose between Hybrid, Semantic, or Keyword search
3. **Text Search**: Enter keywords in the search box
4. **View Results**: Click on any note record to edit

### Import/Export Notes
- **📤 Export Notes**: Download search results as CSV with timestamp
- **📥 Import Notes**: Upload CSV files to bulk import notes
  - Required: `note_name` column
  - Optional: `note`, `url`, `url2`, `url3`, `note_type`, `note_status`, `tags`, `is_active`
  - Duplicate detection uses composite key (`note_name` + `note_type`)
  - Options: Skip duplicates or update existing notes
  - Automatic search index refresh after import

### Advanced Features
- **Manual Index Refresh**: Use sidebar button for troubleshooting
- **Tag Management**: View all available tags organized by usage

## 🏗️ Architecture

### Core Components
- **Frontend**: Streamlit with custom UI components
- **Database**: SQLite with structured schema
- **Search Engine**: FAISS vector store + sentence transformers
- **Backend Logic**: Python with pandas for data processing

### File Structure
```
src/
├── Welcome.py              # Main entry point
├── pages/
│   └── 1-📝Notes.py       # Notes page with search & CRUD
├── utils.py               # Core utilities & semantic search
├── ui_layout.py           # UI components & form layouts
├── migrate_vector_index.py # Initial index migration
├── schema/
│   └── tables_ddl.sql     # Database schema
└── db/
    ├── notes.sqlite3      # SQLite database
    └── notes_faiss.index  # FAISS vector index
```

### Database Schema
```sql
CREATE TABLE t_note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_name TEXT NOT NULL,
    note TEXT,
    url TEXT,
    url2 TEXT,
    url3 TEXT,
    local TEXT,                    -- Local references/paths
    note_type TEXT DEFAULT '',     -- Trinity domain classification
    note_status TEXT DEFAULT '',   -- Workflow status
    tags TEXT,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT NOT NULL,
    updated_by TEXT
);
```

### Note Types (Trinity Framework)
```python
"NOTE_TYPE": [
    'log', 'learning', 'research',           # Knowledge & Process
    'project', 'task',                       # Product & Process  
    'person', 'organization', 'community',   # People Domain
    'event', 'meeting',                      # Process & Events
    'application', 'startup',                # Product Domain
    'others'                                 # Flexible catch-all
]
```

## 🔧 Configuration

### Embedding Model
- Default: `all-MiniLM-L6-v2` (lightweight, fast)
- Configurable in `utils.py` → `CFG["EMBEDDING_MODEL"]`

### Search Parameters
- Similarity threshold: 0.3 (adjustable in `semantic_search()`)
- Top-K results: 10 (configurable per search)

## 🛠️ Development

### Running in Development Mode
```bash
cd src
streamlit run Welcome.py # --server.headless false
```

### Rebuilding Search Index
```bash
cd src
python migrate_vector_index.py
```

### Adding New Features
1. Database changes: Update `db/tables_ddl.sql`
2. UI changes: Modify `pages/` or `ui_layout.py`
3. Search logic: Extend functions in `utils.py`

## 📦 Dependencies

### Core Libraries
- `streamlit` - Web application framework
- `pandas` - Data manipulation
- `sqlite3` - Database operations
- `sentence-transformers` - Text embeddings
- `faiss-cpu` - Vector similarity search
- `streamlit-aggrid` - Enhanced data grids

### Full Requirements
See `requirements.txt` for complete dependency list.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Enterprise Vision & Future Evolution

Smart Notes represents the future of enterprise information management:

### AI-Native Architecture Benefits
1. **Semantic Intelligence**: AI discovers relationships and patterns
2. **Domain Flexibility**: Single platform supports multiple business domains  
3. **Natural Evolution**: System grows with organizational needs
4. **Cross-Domain Insights**: Break down traditional data silos
5. **Future-Ready Architecture**: Foundation for specialized applications

### Evolution Path
```
Generic Note Foundation → Specialized Domain Views
├── Project Management (project, task types)
├── Contact Management (person, organization types)  
├── Product/App Management (application, startup types)
├── Event Management (event, meeting types)
└── Knowledge Base (learning, research types)
```

### Technical Excellence
- **Vector Search**: State-of-the-art semantic similarity
- **Hybrid Approach**: Best of both traditional and AI-powered search
- **Scalable Design**: Handles growing content and complexity
- **User-Centric**: Simple interface hiding sophisticated AI capabilities

## 🚀 Future Enhancements

### Unified Database Architecture
Future versions could migrate to **PostgreSQL + pgvector** for a unified solution combining both RDBMS and vector capabilities:

- **Single database** instead of SQLite + FAISS
- **Native vector operations** with similarity search
- **Advanced SQL queries** with vector filtering
- **Better scalability** and concurrent access
- **ACID compliance** for data integrity

### Specialized Domain Applications
- **Project Management Suite**: Gantt charts, resource allocation
- **Contact Relationship Mapping**: Network analysis, expertise graphs
- **Product Portfolio Dashboard**: Roadmaps, competitive analysis
- **Event & Meeting Intelligence**: Calendar integration, action tracking
- **Knowledge Graph Visualization**: Concept relationships, learning paths

## 🙏 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) for semantic embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for efficient vector search
- [Streamlit](https://streamlit.io/) for the amazing web framework
- The open-source community for excellent tools and libraries

---

**Built with ❤️ using Claude Code and Streamlit**
