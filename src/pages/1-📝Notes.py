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
    filter_col1, search_col2, mode_col3, stat_col4 = st.columns([2, 3, 1, 2])
    
    with filter_col1:
        search_tags = st.multiselect("Filter by tags:", options=tags, default=[])

    with search_col2:
        search_query = st.text_input("Search in notes (name, content, tags):", placeholder="Enter search terms...")
    
    with mode_col3:
        search_mode = st.selectbox("Search mode:", options=["Hybrid", "Semantic", "Keyword"], index=0)

    df = None
    semantic_results = []
    
    # Handle semantic search
    if search_query and search_query.strip() and search_mode in ["Hybrid", "Semantic"]:
        semantic_results = semantic_search(search_query.strip(), top_k=20)
    
    with DBConn() as _conn:
        where_conditions = []
        
        # Handle keyword/text search
        if search_query and search_query.strip() and search_mode in ["Hybrid", "Keyword"]:
            search_term = escape_single_quote(search_query.strip())
            where_conditions.append(f"""
                (note_name LIKE '%{search_term}%' 
                OR note LIKE '%{search_term}%' 
                OR tags LIKE '%{search_term}%')
            """)
        
        # Handle semantic search results
        if semantic_results and search_mode in ["Hybrid", "Semantic"]:
            semantic_ids = [str(result['note_id']) for result in semantic_results]
            where_conditions.append(f"id IN ({','.join(semantic_ids)})")
        
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
                , tags
                , is_active
                , updated_at
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
        if (search_query or search_tags) and df is not None and not df.empty:
            mode_emoji = "🔀" if search_mode == "Hybrid" else "🧠" if search_mode == "Semantic" else "📝"
            st.success(f"{mode_emoji} {len(df)} match found")

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
        st.markdown("##### 🔧 Advanced Options")
        
        refresh_tooltip = """Use this button only when needed:
        
1. **Recovery scenarios** - If the index file gets corrupted or deleted
2. **Bulk operations** - If someone manually modifies the database outside the app  
3. **Troubleshooting** - When users want to force a rebuild to fix search issues
4. **Development/admin** - Useful during development or maintenance

*Note: The search index automatically updates when you save/edit/delete notes through the app.*"""
        
        if st.button("🔄 Refresh Search Index", help=refresh_tooltip):
            refresh_faiss_index()

    c_1, c_2 = st.columns([3,3])
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
