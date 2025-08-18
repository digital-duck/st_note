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
                                   clickable_columns=["url"],
                                   selection_mode="single")
    selected_rows = grid_resp['selected_rows']

    selected_row = None if selected_rows is None or len(selected_rows) < 1 else selected_rows.to_dict(orient='records')[0]

    # display form
    ui_layout_form(selected_row, TABLE_NAME)
    
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

    c_1, c_2 = st.columns([1,3])
    with c_1:
        if df is not None and not df.empty:
            st.download_button(
                label="Download CSV",
                data=df_to_csv(df, index=False),
                file_name=f"notes-{get_ts_now()}.csv",
                mime='text/csv',
            )
    with c_2:
        if tags:
            tag_str = " , ".join(tags)  # tags are already sorted and unique from get_tags()
            st.markdown(f"""
                ##### Available Tags ({len(tags)})
                {tag_str}
            """, unsafe_allow_html=True)
        else:
            st.markdown("##### No tags found")

def main():
    try:
        do_note()
    except Exception as e:
        st.error(str(e))   

if __name__ == '__main__':
    main()
