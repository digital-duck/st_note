from utils import *

st.set_page_config(layout="wide")
st.subheader("Notes 📝")

DB_URL = CFG["META_DB_URL"]
TABLE_NAME = CFG["TABLE_NOTE"]
KEY_PREFIX = f"col_{TABLE_NAME}"

def get_tags():
    """Get all unique individual tags from notes, splitting multi-tag strings"""
    with DBConn() as _conn:
        sql_stmt = f"""
            select 
                distinct tags
            from {TABLE_NAME}
            where tags is not null and tags != ''
            ;
        """
        tag_strings = pd.read_sql(sql_stmt, _conn)["tags"].to_list()
    
    # Split and collect unique individual tags
    unique_tags = set()
    for tag_string in tag_strings:
        if tag_string and tag_string.strip():
            # Split by comma and/or space, then clean up each tag
            tags = []
            # First split by comma
            for part in tag_string.split(','):
                # Then split by space and add each word
                tags.extend(part.split())
            
            # Clean and add non-empty tags
            for tag in tags:
                cleaned_tag = tag.strip().upper()  # Convert to uppercase for consistency
                if cleaned_tag:
                    unique_tags.add(cleaned_tag)
    
    return sorted(list(unique_tags))

def import_notes_from_csv(import_df, skip_duplicates=True, update_existing=False):
    """Import notes from CSV DataFrame with validation and error handling"""
    
    # Define expected columns and their defaults
    expected_columns = {
        'note_name': '',
        'note': '',
        'url': '',
        'url2': '',
        'url3': '',
        'note_type': '',
        'tags': '',
        'is_active': 1
    }
    
    # Prepare import data
    success_count = 0
    error_count = 0
    skip_count = 0
    update_count = 0
    errors = []
    
    # Progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for index, row in import_df.iterrows():
            try:
                # Update progress
                progress = (index + 1) / len(import_df)
                progress_bar.progress(progress)
                note_display = f"{row.get('note_name', 'Unnamed')}"
                if row.get('note_type'):
                    note_display += f" ({row.get('note_type')})"
                status_text.text(f"Processing row {index + 1}/{len(import_df)}: {note_display}")
                
                # Validate required fields
                if not row.get('note_name') or pd.isna(row.get('note_name')):
                    errors.append(f"Row {index + 1}: Missing note_name")
                    error_count += 1
                    continue
                
                # Check for duplicates using composite key (note_name, note_type)
                note_name = str(row['note_name']).strip()
                note_type = str(row.get('note_type', '')).strip()
                
                # Check if note with same name AND type already exists
                with DBConn() as _conn:
                    check_sql = f"""
                        SELECT id FROM {TABLE_NAME} 
                        WHERE note_name = '{escape_single_quote(note_name)}'
                        AND note_type = '{escape_single_quote(note_type)}'
                        LIMIT 1
                    """
                    existing = pd.read_sql(check_sql, _conn)
                
                if not existing.empty:
                    if skip_duplicates and not update_existing:
                        skip_count += 1
                        continue
                    elif update_existing:
                        # Update existing note
                        existing_id = existing.iloc[0]['id']
                        update_data = {
                            'table_name': TABLE_NAME,
                            'id': existing_id,
                            'updated_at': get_ts_now(),
                            'updated_by': DEFAULT_USER
                        }
                        
                        # Add all available columns from CSV
                        for col, default_val in expected_columns.items():
                            if col in row and not pd.isna(row[col]):
                                update_data[col] = str(row[col]).strip()
                            elif col not in ['table_name', 'id', 'updated_at', 'updated_by']:
                                update_data[col] = default_val
                        
                        db_update_by_id(update_data, update_changed=False)
                        update_count += 1
                        continue
                
                # Prepare new note data
                note_data = {
                    'table_name': TABLE_NAME,
                    'created_at': get_ts_now(),
                    'updated_at': get_ts_now(),
                    'created_by': DEFAULT_USER,
                    'updated_by': DEFAULT_USER
                }
                
                # Add all available columns from CSV
                for col, default_val in expected_columns.items():
                    if col in row and not pd.isna(row[col]):
                        note_data[col] = str(row[col]).strip()
                    else:
                        note_data[col] = default_val
                
                # Insert new note
                db_upsert(note_data)
                success_count += 1
                
            except Exception as row_error:
                error_count += 1
                errors.append(f"Row {index + 1} ({row.get('note_name', 'Unknown')}): {str(row_error)}")
                logging.error(f"Import error on row {index + 1}: {row_error}")
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Show results
        if success_count > 0:
            st.success(f"✅ Successfully imported {success_count} notes!")
        if update_count > 0:
            st.info(f"🔄 Updated {update_count} existing notes")
        if skip_count > 0:
            st.warning(f"⏭️ Skipped {skip_count} duplicate notes")
        if error_count > 0:
            st.error(f"❌ Failed to import {error_count} notes")
            
            # Show first few errors
            if errors:
                with st.expander("🐛 Error Details", expanded=False):
                    for error in errors[:10]:  # Show first 10 errors
                        st.text(error)
                    if len(errors) > 10:
                        st.text(f"... and {len(errors) - 10} more errors")
        
        # Refresh search index if any notes were imported/updated
        if success_count > 0 or update_count > 0:
            try:
                selected_model = st.session_state.get("embedding_model", CFG["DEFAULT_EMBEDDING_MODEL"])
                refresh_faiss_index(show_messages=False, model_name=selected_model)
                st.success("🔍 Search index updated automatically!")
            except Exception as idx_error:
                st.warning(f"Notes imported but search index update failed: {idx_error}")
        
        # Auto-refresh the page data
        if success_count > 0 or update_count > 0:
            st.rerun()
            
    except Exception as e:
        st.error(f"Import failed: {str(e)}")
        logging.error(f"CSV import error: {e}")
        progress_bar.empty()
        status_text.empty()

def do_note():
    # get distinct tags
    tags = get_tags()

    # st.markdown("### 🔍 Search Notes")
    filter_types, filter_tags, search_col2, mode_col3, stat_col4 = st.columns([1, 1, 2, 1, 1])

    with filter_types:
        search_types = st.multiselect("Filter by types:", options=CFG["NOTE_TYPE"], default=[])

    with filter_tags:
        search_tags = st.multiselect("Filter by tags:", options=tags, default=[])

    with search_col2:
        search_query = st.text_input("Search in Name, Description, URL:", placeholder="Enter search terms...")
    
    with mode_col3:
        search_mode = st.selectbox("Search mode:", options=["Hybrid", "Keyword", "Semantic"], index=0)

    df = None
    semantic_results = []
    
    # Handle semantic search
    if search_query and search_query.strip() and search_mode in ["Hybrid", "Semantic"]:
        top_k = st.session_state.get("top_k", 10)
        score_threshold = st.session_state.get("score_threshold", 0.3)
        selected_model = st.session_state.get("embedding_model", CFG["DEFAULT_EMBEDDING_MODEL"])
        semantic_results = semantic_search(search_query.strip(), top_k=top_k, score_threshold=score_threshold, model_name=selected_model)
    
    with DBConn() as _conn:
        where_conditions = []
        search_conditions = []  # For combining keyword + semantic
        
        # Handle keyword/text search
        if search_query and search_query.strip() and search_mode in ["Hybrid", "Keyword"]:
            search_term = escape_single_quote(search_query.strip())
            keyword_condition = f"""
                (note_name LIKE '%{search_term}%' 
                OR note LIKE '%{search_term}%'
                OR url LIKE '%{search_term}%')
            """
            if search_mode == "Keyword":
                where_conditions.append(keyword_condition)
            else:  # Hybrid mode
                search_conditions.append(keyword_condition)
        
        # Handle semantic search results
        if search_mode in ["Hybrid", "Semantic"]:
            if semantic_results:
                semantic_ids = [str(result['note_id']) for result in semantic_results]
                semantic_condition = f"id IN ({','.join(semantic_ids)})"
                if search_mode == "Semantic":
                    where_conditions.append(semantic_condition)
                else:  # Hybrid mode
                    search_conditions.append(semantic_condition)
            elif search_mode == "Semantic":
                # For semantic-only mode with no results, return nothing
                where_conditions.append("id = -1")  # This will match no rows
        
        # Combine search conditions with OR for hybrid mode
        if search_conditions:
            where_conditions.append(f"({' OR '.join(search_conditions)})")
        
        if search_types:
            typ_conditions = []
            for typ in search_types:
                escaped_typ = escape_single_quote(typ)
                typ_conditions.append(f" note_type LIKE '%{escaped_typ}%'")
            where_conditions.append(f"({' OR '.join(typ_conditions)})")

        if search_tags:
            tag_conditions = []
            for tag in search_tags:
                escaped_tag = escape_single_quote(tag)
                # Use word boundaries to match individual tags (case-insensitive)
                tag_conditions.append(f"UPPER(tags) LIKE '%{escaped_tag.upper()}%'")
            where_conditions.append(f"({' OR '.join(tag_conditions)})")
        
        where_clause = ""
        if where_conditions:
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
        
        sql_stmt = f"""
            select 
                note_name
                , note 
                , url 
                , url2 
                , url3 
                , note_type
                , tags
                , updated_at
                , is_active
                , id
            from {TABLE_NAME}
            {where_clause}
            order by updated_at desc
            ;
        """
        df = pd.read_sql(sql_stmt, _conn)
        
        # For semantic-only search, order by similarity score
        if search_mode == "Semantic" and semantic_results:
            score_map = {result['note_id']: result['similarity_score'] for result in semantic_results}
            df['similarity_score'] = df['id'].map(score_map)
            df = df.sort_values('similarity_score', ascending=False).drop('similarity_score', axis=1)

    with stat_col4:
        if (search_query or search_tags or search_types) and df is not None and not df.empty:
            mode_emoji = "🔀" if search_mode == "Hybrid" else "🧠" if search_mode == "Semantic" else "📝"
            st.success(f"{mode_emoji} {len(df)} match(s)")

    grid_resp = ui_display_df_grid(df, 
                                   clickable_columns=["url","url2","url3"],
                                   selection_mode="single")
    selected_rows = grid_resp['selected_rows']

    selected_row = None if selected_rows is None or len(selected_rows) < 1 else selected_rows.to_dict(orient='records')[0]
    # display form
    ui_layout_form(selected_row, TABLE_NAME)
    
    st.divider()


    c_2, c_1, c_3 = st.columns([2,2,4])
    with c_1:
        with st.expander("Export Notes to CSV", expanded=False):
            if df is not None and not df.empty:
                st.download_button(
                    label="Export",
                    data=df_to_csv(df, index=False),
                    file_name=f"notes-{get_ts_now()}.csv",
                    mime='text/csv',
                    help="Export notes to share",
                    type="primary"
                )
    with c_2:
        with st.expander("Import Notes from CSV", expanded=False):

            # CSV Import functionality
            uploaded_file = st.file_uploader(
                "Import",
                type=['csv'],
                help="Upload a CSV file with notes. Required: note_name. Optional: note, url, url2, url3, note_type, tags. Duplicates detected by (note_name + note_type) combination.",
                key="csv_import"
            )
        
            if uploaded_file is not None:
                try:
                    # Read uploaded CSV
                    import_df = pd.read_csv(uploaded_file)
                    
                    # Validate required columns
                    required_cols = ['note_name']
                    missing_cols = [col for col in required_cols if col not in import_df.columns]
                    
                    if missing_cols:
                        st.error(f"Missing required columns: {', '.join(missing_cols)}")
                    else:
                        # Show preview
                        st.success(f"📁 Ready to import {len(import_df)} notes")
                        
                        # Data preview
                        with st.expander("📋 Preview Import Data", expanded=False):
                            st.dataframe(import_df.head(10))
                            if len(import_df) > 10:
                                st.info(f"Showing first 10 rows. Total: {len(import_df)} rows")
                        
                        # Import options
                        col_opt2, col_opt1 = st.columns(2)
                        with col_opt1:
                            skip_duplicates = st.checkbox(
                                "Skip duplicates", 
                                value=True,
                                help="Skip notes with same (note_name + note_type) combination"
                            )
                        with col_opt2:
                            update_existing = st.checkbox(
                                "Update existing", 
                                value=True,
                                help="Update notes if (note_name + note_type) combination already exists"
                            )
                        
                        # Import button
                        if st.button("🚀 Import Notes", type="primary"):
                            import_notes_from_csv(import_df, skip_duplicates, update_existing)
                            
                except Exception as e:
                    st.error(f"Error reading CSV file: {str(e)}")
                    st.info("Please ensure your CSV file is properly formatted with UTF-8 encoding.")

    with c_3:
        with st.expander("Display Tags", expanded=False):
            if tags:
                tag_str = " | ".join(tags)  # tags are already sorted and unique from get_tags()
                st.markdown(f"""
                    ##### Tags ({len(tags)})
                    {tag_str}
                """, unsafe_allow_html=True)
            else:
                st.markdown("##### No tags found")

def show_sidebar():
    # Sidebar - Advanced Options
    with st.sidebar:
        # st.markdown("---")
       
        # Semantic search parameters
        st.markdown("#### 🔧 **Semantic Search Settings**")
        
        # Embedding model selection
        model_options = list(CFG["EMBEDDING_MODELS"].keys())
        st.selectbox("Embedding Model", options=model_options, 
                    index=model_options.index(CFG["DEFAULT_EMBEDDING_MODEL"]),
                    help="English (Fast): Optimized for English-only content\nMultilingual (EN+CN): Supports Chinese and English with cross-language search",
                    key="embedding_model")
        
        st.slider("Max Results (top_k)", min_value=5, max_value=50, value=10, step=5,
                 help="Maximum number of results to return from semantic search", key="top_k")
        
        st.slider("Similarity Threshold", min_value=0.0, max_value=1.0, value=0.3, step=0.1,
                 help="Minimum similarity score (0.0 = very loose, 1.0 = exact match)", key="score_threshold")
        
        st.markdown("---")
        
        refresh_tooltip = """Use this button only when needed:
        
1. **Recovery scenarios** - If the index file gets corrupted or deleted
2. **Bulk operations** - If someone manually modifies the database outside the app  
3. **Troubleshooting** - When users want to force a rebuild to fix search issues
4. **Development/admin** - Useful during development or maintenance

*Note: The search index automatically updates when you save/edit/delete notes through the app.*"""
        
        if st.button("🔄 Refresh Search Index", help=refresh_tooltip):
            selected_model = st.session_state.get("embedding_model", CFG["DEFAULT_EMBEDDING_MODEL"])
            refresh_faiss_index(model_name=selected_model)

def main():
    try:
        show_sidebar()
        do_note()
    except Exception as e:
        st.error(str(e))   

if __name__ == '__main__':
    main()
