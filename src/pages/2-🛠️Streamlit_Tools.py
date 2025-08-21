#!/usr/bin/env python3
"""
🛠️ Streamlit Tools - The Meta-Application
Visual designer for creating Streamlit applications dynamically

"Applications that build applications" - The future of low-code development!
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import *
from ui_layout import COLUMN_PROPS

# Import our generators
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'streamlit_tools', 'generators'))
from page_generator import StreamlitPageGenerator

# Page configuration
st.set_page_config(
    page_title="🛠️ Streamlit Tools",
    page_icon="🛠️",
    layout="wide"
)

def main():
    """Main Streamlit Tools interface"""
    
    # Header
    st.title("🛠️ Streamlit Tools")
    st.markdown("**The Meta-Application: Build Streamlit Apps Visually**")
    st.markdown("*Transform your ideas into working applications through visual design*")
    
    # Initialize generator
    if 'generator' not in st.session_state:
        st.session_state.generator = StreamlitPageGenerator()
    
    generator = st.session_state.generator
    
    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview", 
        "🏗️ Schema Designer", 
        "🎨 UI Layout Designer", 
        "🚀 Page Generator", 
        "📊 Management"
    ])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_schema_designer(generator)
    
    with tab3:
        show_ui_layout_designer(generator)
    
    with tab4:
        show_page_generator(generator)
    
    with tab5:
        show_management_panel(generator)

def show_database_migration_tool():
    """Database migration tool for UI configurations"""
    st.subheader("🗄️ Database Migration Tool")
    st.markdown("Migrate existing UI configurations to database-driven architecture")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Available Tables in ui_layout.py")
        
        try:
            from ui_layout import COLUMN_PROPS
            
            available_tables = list(COLUMN_PROPS.keys())
            if available_tables:
                for table_name in available_tables:
                    with st.expander(f"📋 {table_name}", expanded=False):
                        props = COLUMN_PROPS[table_name]
                        st.write(f"**Columns**: {len(props)}")
                        st.write(f"**Sample columns**: {list(props.keys())[:5]}")
                        
                        if st.button(f"🚀 Migrate {table_name} to Database", key=f"migrate_{table_name}"):
                            migrate_table_to_db(table_name, props)
            else:
                st.info("No tables found in ui_layout.py")
                
        except ImportError:
            st.error("Could not import ui_layout.py")
    
    with col2:
        st.markdown("### Migration Status")
        
        # Check database migration status
        try:
            # Check if ui_layout_config table exists
            if db_table_exists("t_ui_layout_config"):
                st.success("✅ Migration table ready")
                
                # Show migrated tables
                with DBConn() as conn:
                    sql = "SELECT DISTINCT table_name, COUNT(*) as columns FROM t_ui_layout_config GROUP BY table_name"
                    df = pd.read_sql(sql, conn)
                    
                    if not df.empty:
                        st.markdown("**Migrated Tables:**")
                        for _, row in df.iterrows():
                            st.write(f"📊 {row['table_name']}: {row['columns']} columns")
                    else:
                        st.info("No tables migrated yet")
            else:
                st.warning("⚠️ Migration table not found")
                if st.button("🔧 Create Migration Table"):
                    if create_ui_layout_table():
                        st.success("Migration table created!")
                        st.rerun()
                        
        except Exception as e:
            st.error(f"Database check failed: {e}")
        
        # Migration tools
        st.markdown("### Tools")
        if st.button("🔄 Compile UI from Database"):
            if compile_ui_layout_from_db():
                st.success("UI layout compiled successfully!")
            else:
                st.error("Compilation failed")

def migrate_table_to_db(table_name, column_props):
    """Migrate a specific table configuration to database"""
    try:
        if migrate_column_props_to_db(table_name, column_props):
            st.success(f"✅ Migrated {table_name} to database successfully!")
            
            # Show migration details
            with st.expander("Migration Details", expanded=True):
                st.write(f"**Table**: {table_name}")
                st.write(f"**Columns migrated**: {len(column_props)}")
                st.write(f"**Timestamp**: {datetime.now().isoformat()}")
                
                # Show sample migrated config
                sample_config = load_ui_config_from_db(table_name)
                if sample_config:
                    st.json(dict(list(sample_config.items())[:2]))  # Show first 2 columns
        else:
            st.error(f"❌ Failed to migrate {table_name}")
            
    except Exception as e:
        st.error(f"Migration error: {e}")

def show_overview():
    """Show overview and introduction to Streamlit Tools"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🎯 Welcome to Streamlit Tools")
        
        st.markdown("""
        **Streamlit Tools** is a revolutionary meta-application that allows you to build 
        complete Streamlit applications through visual design. No more writing boilerplate 
        code - just design your data models and UI layouts, and watch your applications 
        come to life!
        
        ### 🚀 What You Can Build
        - **Contact Management Systems** 📇
        - **Project Tracking Applications** 📊  
        - **Knowledge Bases** 📚
        - **Event Management Tools** 📅
        - **Custom Domain Applications** 🎯
        
        ### ✨ Key Features
        - **Visual Schema Design**: Create database tables through intuitive forms
        - **Drag-and-Drop UI Builder**: Design forms without coding
        - **Automatic Code Generation**: Get production-ready Streamlit pages
        - **Hot-Reload Integration**: See changes instantly
        - **Trinity Framework**: Built on People-Product-Process domains
        """)
        
        st.subheader("🏗️ The Magic Workflow")
        
        # Visual workflow representation
        workflow_steps = [
            ("🎯 Define", "What you want to build"),
            ("🏗️ Design", "Schema and UI layout"),  
            ("⚙️ Configure", "Features and behaviors"),
            ("🚀 Generate", "Complete Streamlit page"),
            ("✨ Deploy", "Working application!")
        ]
        
        for i, (icon, desc) in enumerate(workflow_steps):
            if i > 0:
                st.write("↓")
            st.write(f"**{icon} {desc}**")
    
    with col2:
        st.header("📊 Quick Stats")
        
        # Get available schemas
        try:
            schemas = st.session_state.generator.list_available_schemas()
            
            # Stats
            st.metric("Available Schemas", len(schemas))
            st.metric("Generated Pages", count_generated_pages())
            st.metric("Active Features", "5")
            
            st.subheader("📋 Available Schemas")
            for schema in schemas:
                st.write(f"{schema['icon']} **{schema['display_name']}**")
                if schema['description']:
                    st.caption(schema['description'])
                    
        except Exception as e:
            st.error(f"Error loading schemas: {e}")
        
        st.subheader("🔗 Quick Actions")
        if st.button("🎯 Create New Schema"):
            st.session_state.active_tab = "schema_designer"
            st.rerun()
        
        if st.button("🚀 Generate Page"):
            st.session_state.active_tab = "page_generator"
            st.rerun()

def show_schema_designer(generator):
    """Visual schema designer interface"""
    
    st.header("🏗️ Schema Designer")
    st.markdown("Design your database schema through an intuitive visual interface")
    
    # Schema designer form
    with st.form("schema_designer", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 Table Definition")
            
            # Basic table info
            table_name = st.text_input(
                "Table Name",
                placeholder="t_contacts",
                help="Technical table name (e.g., t_contacts, t_projects)"
            )
            
            display_name = st.text_input(
                "Display Name",
                placeholder="📇 Contacts",
                help="User-friendly name with emoji (e.g., 📇 Contacts)"
            )
            
            description = st.text_area(
                "Description",
                placeholder="Contact and relationship management system",
                help="Brief description of what this table/application manages"
            )
            
            icon = st.text_input(
                "Icon",
                placeholder="📇",
                help="Emoji icon for the menu"
            )
            
            menu_position = st.number_input(
                "Menu Position",
                min_value=1,
                max_value=99,
                value=10,
                help="Position in the Streamlit menu"
            )
            
            # Trinity framework classification
            trinity_domain = st.selectbox(
                "Trinity Domain",
                ["People", "Product", "Process", "Mixed"],
                help="Primary domain classification"
            )
        
        with col2:
            st.subheader("⚙️ Features")
            
            # Feature checkboxes
            features = {}
            features['semantic_search'] = st.checkbox("🧠 Semantic Search", value=True)
            features['import_export'] = st.checkbox("📥📤 Import/Export", value=True)
            features['tag_management'] = st.checkbox("🏷️ Tag Management", value=True)
            features['url_linking'] = st.checkbox("🔗 URL Linking", value=True)
            features['audit_trail'] = st.checkbox("📝 Audit Trail", value=True)
        
        # Column designer
        st.subheader("📊 Column Designer")
        
        # Initialize columns in session state
        if f"{table_name}_columns" not in st.session_state:
            st.session_state[f"{table_name}_columns"] = [
                {"name": "id", "type": "INTEGER", "constraints": ["PRIMARY KEY", "AUTOINCREMENT"]},
                {"name": f"{table_name.replace('t_', '')}_name", "type": "TEXT", "constraints": ["NOT NULL"]},
            ]
        
        # Column management
        columns_data = st.session_state[f"{table_name}_columns"]
        
        # Add column interface (outside the form)
        if st.checkbox("➕ Add New Column", key="show_add_column"):
            col_col1, col_col2, col_col3 = st.columns(3)
            
            with col_col1:
                new_col_name = st.text_input("Column Name", key="new_col_name")
                new_col_type = st.selectbox("Data Type", ["TEXT", "INTEGER", "REAL", "BLOB"], key="new_col_type")
            
            with col_col2:
                new_col_constraints = st.multiselect(
                    "Constraints",
                    ["NOT NULL", "PRIMARY KEY", "AUTOINCREMENT", "UNIQUE"],
                    key="new_col_constraints"
                )
                new_col_default = st.text_input("Default Value", key="new_col_default")
            
            with col_col3:
                new_col_description = st.text_area("Description", key="new_col_description")
                
                if st.button("➕ Add Column"):
                    if new_col_name:
                        new_column = {
                            "name": new_col_name,
                            "type": new_col_type,
                            "constraints": new_col_constraints + ([f"DEFAULT '{new_col_default}'"] if new_col_default else []),
                            "description": new_col_description
                        }
                        st.session_state[f"{table_name}_columns"].append(new_column)
                        st.rerun()
        
        # Display current columns
        if columns_data:
            st.subheader("📋 Current Columns")
            columns_df = pd.DataFrame(columns_data)
            edited_columns = st.data_editor(
                columns_df,
                use_container_width=True,
                num_rows="dynamic",
                key="columns_editor"
            )
            st.session_state[f"{table_name}_columns"] = edited_columns.to_dict('records')
        
        # Generate schema button
        if st.form_submit_button("💾 Save Schema"):
            if table_name and display_name:
                schema_data = {
                    "table_name": table_name,
                    "display_name": display_name,
                    "description": description,
                    "icon": icon,
                    "menu_position": menu_position,
                    "trinity_domain": trinity_domain,
                    "columns": st.session_state[f"{table_name}_columns"],
                    "features": features,
                    "created_at": datetime.now().isoformat()
                }
                
                # Save schema file
                save_schema(generator, table_name, schema_data)
                st.success(f"✅ Schema saved: {table_name}")
                st.rerun()
            else:
                st.error("Please fill in Table Name and Display Name")

def show_ui_layout_designer(generator):
    """Visual UI layout designer"""
    
    st.header("🎨 UI Layout Designer")
    st.markdown("Design the user interface layout for your application")
    
    # Schema selector
    try:
        schemas = generator.list_available_schemas()
        if not schemas:
            st.warning("⚠️ No schemas found. Create a schema first in the Schema Designer tab.")
            return
        
        schema_options = {f"{s['icon']} {s['display_name']}": s['table_name'] for s in schemas}
        selected_schema_display = st.selectbox("Select Schema", list(schema_options.keys()))
        selected_table = schema_options[selected_schema_display]
        
        # Load selected schema
        schema = generator.load_schema(selected_table)
        
        st.subheader(f"🎨 Designing UI for {schema['display_name']}")
        
        # Form layout designer
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 Form Layout")
            
            # Show columns in a grid layout
            columns = schema['columns']
            system_columns = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'is_active']
            
            # Filter out system columns for UI design
            user_columns = [col for col in columns if col['name'] not in system_columns]
            
            for i, column in enumerate(user_columns):
                with st.expander(f"🔧 {column['name']} Configuration", expanded=False):
                    config_col1, config_col2 = st.columns(2)
                    
                    with config_col1:
                        widget_type = st.selectbox(
                            "Widget Type",
                            ["text_input", "text_area", "selectbox", "multiselect", "date_input", "number_input"],
                            key=f"widget_{column['name']}"
                        )
                        
                        label_text = st.text_input(
                            "Label Text",
                            value=column['name'].replace('_', ' ').title(),
                            key=f"label_{column['name']}"
                        )
                        
                        form_column = st.selectbox(
                            "Form Column",
                            [f"COL_{i}-{j}" for i in range(1, 5) for j in range(1, 4)],
                            index=i % 12,
                            key=f"form_col_{column['name']}"
                        )
                    
                    with config_col2:
                        tooltip = st.text_area(
                            "Tooltip",
                            value=column.get('description', ''),
                            key=f"tooltip_{column['name']}"
                        )
                        
                        is_required = st.checkbox(
                            "Required",
                            value='NOT NULL' in column.get('constraints', []),
                            key=f"required_{column['name']}"
                        )
                        
                        is_clickable = st.checkbox(
                            "Clickable (for URLs)",
                            value='url' in column['name'].lower(),
                            key=f"clickable_{column['name']}"
                        )
        
        with col2:
            st.subheader("👀 Live Preview")
            
            st.markdown("**Form Layout Preview:**")
            
            # Show a mock form preview
            with st.container():
                preview_col1, preview_col2 = st.columns(2)
                
                with preview_col1:
                    st.markdown("**Column 1 & 2**")
                    for column in user_columns[:len(user_columns)//2]:
                        widget_type = st.session_state.get(f"widget_{column['name']}", "text_input")
                        label = st.session_state.get(f"label_{column['name']}", column['name'].title())
                        
                        if widget_type == "text_input":
                            st.text_input(label, disabled=True, key=f"preview_{column['name']}")
                        elif widget_type == "text_area":
                            st.text_area(label, disabled=True, key=f"preview_{column['name']}")
                        elif widget_type == "selectbox":
                            st.selectbox(label, ["Option 1", "Option 2"], disabled=True, key=f"preview_{column['name']}")
                
                with preview_col2:
                    st.markdown("**Column 3 & 4**")
                    for column in user_columns[len(user_columns)//2:]:
                        widget_type = st.session_state.get(f"widget_{column['name']}", "text_input")
                        label = st.session_state.get(f"label_{column['name']}", column['name'].title())
                        
                        if widget_type == "text_input":
                            st.text_input(label, disabled=True, key=f"preview2_{column['name']}")
                        elif widget_type == "text_area":
                            st.text_area(label, disabled=True, key=f"preview2_{column['name']}")
                        elif widget_type == "selectbox":
                            st.selectbox(label, ["Option 1", "Option 2"], disabled=True, key=f"preview2_{column['name']}")
            
            # Generate COLUMN_PROPS button
            if st.button("💾 Generate UI Configuration"):
                generate_ui_config(generator, selected_table, user_columns)
                st.success("✅ UI configuration generated!")
    
    except Exception as e:
        st.error(f"Error in UI designer: {e}")

def show_page_generator(generator):
    """Page generation interface"""
    
    st.header("🚀 Page Generator")
    st.markdown("Generate complete Streamlit pages from your schemas")
    
    # Schema selector
    try:
        schemas = generator.list_available_schemas()
        if not schemas:
            st.warning("⚠️ No schemas found. Create a schema first in the Schema Designer tab.")
            return
        
        # Generation interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📋 Select Schema to Generate")
            
            for schema in schemas:
                with st.expander(f"{schema['icon']} {schema['display_name']}", expanded=False):
                    schema_data = generator.load_schema(schema['table_name'])
                    
                    st.write(f"**Description:** {schema_data.get('description', 'No description')}")
                    st.write(f"**Columns:** {len(schema_data.get('columns', []))}")
                    st.write(f"**Trinity Domain:** {schema_data.get('trinity_domain', 'Not specified')}")
                    
                    # Features
                    features = schema_data.get('features', {})
                    enabled_features = [k for k, v in features.items() if v]
                    if enabled_features:
                        st.write(f"**Features:** {', '.join(enabled_features)}")
                    
                    # Generation buttons
                    gen_col1, gen_col2, gen_col3 = st.columns(3)
                    
                    with gen_col1:
                        if st.button(f"🚀 Generate Page", key=f"gen_{schema['table_name']}"):
                            generate_page_action(generator, schema['table_name'])
                    
                    with gen_col2:
                        if st.button(f"📝 View DDL", key=f"ddl_{schema['table_name']}"):
                            show_ddl_preview(generator, schema['table_name'])
                    
                    with gen_col3:
                        if st.button(f"⚙️ View Config", key=f"config_{schema['table_name']}"):
                            show_config_preview(generator, schema['table_name'])
        
        with col2:
            st.subheader("📊 Generation Status")
            
            # Show generation history or status
            if 'generation_log' not in st.session_state:
                st.session_state.generation_log = []
            
            if st.session_state.generation_log:
                st.markdown("**Recent Generations:**")
                for log_entry in st.session_state.generation_log[-5:]:
                    st.write(f"✅ {log_entry}")
            else:
                st.info("No pages generated yet")
            
            # Quick actions
            st.subheader("⚡ Quick Actions")
            if st.button("🔄 Refresh Schemas"):
                st.rerun()
            
            if st.button("📁 Open Pages Folder"):
                st.info("Pages are located in: src/pages/")
    
    except Exception as e:
        st.error(f"Error in page generator: {e}")

def show_management_panel(generator):
    """Management and maintenance panel"""
    
    st.header("📊 Management Panel")
    st.markdown("Manage your schemas, generated pages, and system configuration")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Schemas", "📄 Generated Pages", "⚙️ System", "🗄️ Database Migration"])
    
    with tab1:
        st.subheader("📋 Schema Management")
        
        try:
            schemas = generator.list_available_schemas()
            
            if schemas:
                for schema in schemas:
                    with st.expander(f"{schema['icon']} {schema['display_name']}", expanded=False):
                        schema_data = generator.load_schema(schema['table_name'])
                        
                        # Schema info
                        info_col1, info_col2 = st.columns(2)
                        
                        with info_col1:
                            st.write(f"**Table:** {schema['table_name']}")
                            st.write(f"**Columns:** {len(schema_data.get('columns', []))}")
                            st.write(f"**Domain:** {schema_data.get('trinity_domain', 'Not specified')}")
                        
                        with info_col2:
                            if st.button(f"🗑️ Delete", key=f"del_{schema['table_name']}"):
                                delete_schema(generator, schema['table_name'])
                                st.rerun()
                            
                            if st.button(f"📝 Edit", key=f"edit_{schema['table_name']}"):
                                st.info("Edit functionality coming soon!")
                        
                        # Show schema JSON
                        if st.checkbox(f"Show JSON", key=f"json_{schema['table_name']}"):
                            st.json(schema_data)
            else:
                st.info("No schemas found")
        
        except Exception as e:
            st.error(f"Error loading schemas: {e}")
    
    with tab2:
        st.subheader("📄 Generated Pages")
        
        # List generated pages
        pages_dir = Path(__file__).parent
        generated_pages = list(pages_dir.glob("*.py"))
        
        st.write(f"Found {len(generated_pages)} pages in /pages directory:")
        
        for page_file in generated_pages:
            page_name = page_file.name
            if page_name != "2-🛠️Streamlit_Tools.py":  # Exclude this file
                st.write(f"📄 {page_name}")
    
    with tab3:
        st.subheader("⚙️ System Configuration")
        
        # System info
        st.write("**Streamlit Tools Status:**")
        st.write(f"✅ Generator: Active")
        st.write(f"✅ Templates: Available")
        st.write(f"✅ Schema Storage: Connected")
        
        # Maintenance actions
        if st.button("🧹 Clean Generated Files"):
            st.info("Cleanup functionality coming soon!")
        
        if st.button("🔄 Rebuild All"):
            st.info("Rebuild functionality coming soon!")
    
    with tab4:
        show_database_migration_tool()
        
        # Add table creation tool
        st.markdown("---")
        st.subheader("🏗️ Database Table Creation")
        
        schemas = generator.list_available_schemas()
        if schemas:
            for schema in schemas:
                with st.expander(f"📊 Create {schema['display_name']} Table", expanded=False):
                    schema_data = generator.load_schema(schema['table_name'])
                    
                    # Show DDL preview
                    ddl = generator.generate_sql_ddl(schema['table_name'])
                    st.code(ddl, language="sql")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"🚀 Create Table", key=f"create_table_{schema['table_name']}"):
                            create_table_from_schema(generator, schema['table_name'])
                    
                    with col2:
                        table_exists = db_table_exists(schema['table_name'])
                        if table_exists:
                            st.success("✅ Table exists")
                        else:
                            st.warning("⚠️ Table missing")
                    
                    with col3:
                        if table_exists and st.button(f"📊 View Data", key=f"view_data_{schema['table_name']}"):
                            show_table_data_preview(schema['table_name'])
        else:
            st.info("No schemas available for table creation")

# Helper functions

def count_generated_pages():
    """Count generated pages in the pages directory"""
    try:
        pages_dir = Path(__file__).parent
        return len(list(pages_dir.glob("*.py"))) - 1  # Exclude this file
    except:
        return 0

def save_schema(generator, table_name, schema_data):
    """Save schema to JSON file"""
    schema_file = generator.schemas_dir / f"{table_name}.json"
    with open(schema_file, 'w') as f:
        json.dump(schema_data, f, indent=2)

def generate_ui_config(generator, table_name, columns):
    """Generate UI configuration for the table"""
    # This would generate the COLUMN_PROPS configuration
    config = generator.generate_column_props(table_name)
    st.success(f"UI configuration generated for {table_name}")
    st.json(config)

def generate_page_action(generator, table_name):
    """Generate a complete Streamlit page"""
    try:
        output_file = generator.generate_page(table_name)
        
        # Log the generation
        if 'generation_log' not in st.session_state:
            st.session_state.generation_log = []
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.generation_log.append(f"{timestamp} - Generated {table_name}")
        
        st.success(f"✅ Page generated: {output_file.name}")
        st.info("🔄 Restart the Streamlit app to see the new page in the menu")
        
    except Exception as e:
        st.error(f"❌ Generation failed: {e}")

def show_ddl_preview(generator, table_name):
    """Show SQL DDL preview"""
    try:
        ddl = generator.generate_sql_ddl(table_name)
        st.code(ddl, language="sql")
    except Exception as e:
        st.error(f"Error generating DDL: {e}")

def show_config_preview(generator, table_name):
    """Show COLUMN_PROPS configuration preview"""
    try:
        config = generator.generate_column_props(table_name)
        st.json(config)
    except Exception as e:
        st.error(f"Error generating config: {e}")

def delete_schema(generator, table_name):
    """Delete a schema file"""
    try:
        schema_file = generator.schemas_dir / f"{table_name}.json"
        if schema_file.exists():
            schema_file.unlink()
            st.success(f"✅ Deleted schema: {table_name}")
        else:
            st.warning(f"Schema file not found: {table_name}")
    except Exception as e:
        st.error(f"Error deleting schema: {e}")

def create_table_from_schema(generator, table_name):
    """Create database table from schema definition"""
    try:
        # Generate DDL
        ddl = generator.generate_sql_ddl(table_name)
        
        # Execute DDL
        if db_create_table_from_ddl(ddl):
            st.success(f"✅ Table {table_name} created successfully!")
            
            # Also create/update UI configuration
            schema_data = generator.load_schema(table_name)
            column_props = generator.generate_column_props(table_name)
            
            # Migrate UI config to database
            if migrate_column_props_to_db(table_name, column_props[table_name]):
                st.success(f"✅ UI configuration migrated for {table_name}")
            
            st.rerun()
        else:
            st.error(f"❌ Failed to create table {table_name}")
            
    except Exception as e:
        st.error(f"Table creation error: {e}")

def show_table_data_preview(table_name):
    """Show preview of table data"""
    try:
        with DBConn() as conn:
            sql = f"SELECT * FROM {table_name} LIMIT 10"
            df = pd.read_sql(sql, conn)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.caption(f"Showing first 10 rows of {table_name}")
            else:
                st.info(f"Table {table_name} is empty")
                
    except Exception as e:
        st.error(f"Error loading table data: {e}")

if __name__ == "__main__":
    main()