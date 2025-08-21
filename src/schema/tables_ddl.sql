-- drop table t_note;
CREATE TABLE if not exists t_note
( 
    id INTEGER PRIMARY KEY AUTOINCREMENT

    , note_name text NOT NULL
	, note text
    , url text 
    , url2 text 
    , url3 text 
    , local text 
	, note_type TEXT DEFAULT ''
	, note_status TEXT DEFAULT ''
	, tags text

	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text
	, updated_at text
	, created_by text  NOT NULL
	, updated_by text  
);

-- Streamlit Tools: UI Layout Configuration Table
-- Stores UI metadata for database-driven dynamic form generation
CREATE TABLE if not exists t_ui_layout_config
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    
    -- UI Properties
    is_system_col INTEGER DEFAULT 0,
    is_user_key INTEGER DEFAULT 0,
    is_required INTEGER DEFAULT 0,
    is_visible INTEGER DEFAULT 1,
    is_editable INTEGER DEFAULT 1,
    is_clickable INTEGER DEFAULT 0,
    
    -- Form Layout
    form_column TEXT,           -- COL_1-1, COL_2-3, etc.
    widget_type TEXT,           -- text_input, selectbox, text_area, etc.
    label_text TEXT,            -- Human-readable label
    tooltip TEXT,               -- Help text
    
    -- Configuration Metadata
    config_version TEXT DEFAULT '1.0',
    datatype TEXT DEFAULT 'text',
    
    -- System fields
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT NOT NULL,
    updated_by TEXT,
    
    UNIQUE(table_name, column_name, config_version)
);

-- select * from t_note;
