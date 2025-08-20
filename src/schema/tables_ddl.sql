-- drop table t_note;
CREATE TABLE if not exists t_note
( 
    id INTEGER PRIMARY KEY AUTOINCREMENT

    , note_name text NOT NULL
	, note text
    , url text 
    , url2 text 
    , url3 text 
	, note_type TEXT DEFAULT ''
	, note_status TEXT DEFAULT ''
	, tags text

	, is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
	, created_at text
	, updated_at text
	, created_by text  NOT NULL
	, updated_by text  
);
-- select * from t_note;
