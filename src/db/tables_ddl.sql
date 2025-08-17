-- drop table t_note;
CREATE TABLE if not exists t_note
( 
    id INTEGER PRIMARY KEY AUTOINCREMENT

    , note_name text NOT NULL
    , url text 
	, note_type TEXT DEFAULT '' CHECK(note_type IN ('', 'learning', 'research', 'project', 'journal'))
	, note text
	, tags text

	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text
	, updated_at text
	, created_by text  NOT NULL -- user email
	, updated_by text  
);
-- select * from t_note;
