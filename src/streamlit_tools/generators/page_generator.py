#!/usr/bin/env python3
"""
Streamlit Tools - Page Generator
Generates complete Streamlit pages from schema definitions and UI layouts

This is the core magic of the meta-application! ✨
"""

import json
import os
from datetime import datetime
from pathlib import Path
from jinja2 import Template
import sys

# Add parent directories to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

class StreamlitPageGenerator:
    """
    The heart of the meta-application - generates Streamlit pages from configurations
    """
    
    def __init__(self):
        self.streamlit_tools_dir = Path(__file__).parent.parent
        self.schemas_dir = self.streamlit_tools_dir / "schemas"
        self.templates_dir = self.streamlit_tools_dir / "templates"
        self.layouts_dir = self.streamlit_tools_dir / "layouts"
        self.pages_dir = src_dir / "pages"
        
    def load_schema(self, table_name):
        """Load schema definition from JSON file"""
        schema_file = self.schemas_dir / f"{table_name}.json"
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        with open(schema_file, 'r') as f:
            return json.load(f)
    
    def load_template(self, template_name="page_template.py"):
        """Load Jinja2 template for page generation"""
        template_file = self.templates_dir / template_name
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        with open(template_file, 'r') as f:
            return Template(f.read())
    
    def generate_page(self, table_name, template_name="page_template.py"):
        """
        Generate a complete Streamlit page from schema definition
        
        This is where the magic happens! 🎭
        """
        print(f"🚀 Generating page for {table_name}...")
        
        # Load schema and template
        schema = self.load_schema(table_name)
        template = self.load_template(template_name)
        
        # Prepare template variables
        template_vars = {
            **schema,  # All schema fields
            'generation_timestamp': datetime.now().isoformat(),
            'generator_version': '1.0.0'
        }
        
        # Generate page content
        page_content = template.render(**template_vars)
        
        # Determine output filename
        menu_position = schema.get('menu_position', 99)
        icon = schema.get('icon', '📄')
        display_name = schema.get('display_name', table_name.title())
        
        # Clean display name for filename (remove emojis and special chars)
        clean_name = ''.join(c for c in display_name if c.isalnum() or c in (' ', '_')).strip()
        clean_name = clean_name.replace(' ', '_')
        
        filename = f"{menu_position}-{icon}{clean_name}.py"
        output_file = self.pages_dir / filename
        
        # Write generated page
        with open(output_file, 'w') as f:
            f.write(page_content)
        
        print(f"✅ Generated page: {output_file}")
        return output_file
    
    def generate_column_props(self, table_name):
        """
        Generate COLUMN_PROPS configuration for ui_layout.py
        """
        schema = self.load_schema(table_name)
        
        # Start with basic column props structure
        column_props = {}
        
        for i, column in enumerate(schema['columns']):
            col_name = column['name']
            col_type = column['type']
            
            # Determine form column position (distribute across 4 columns)
            form_col = f"COL_{(i % 4) + 1}-{(i // 4) + 1}"
            
            # Determine widget type based on column properties
            widget_type = self._determine_widget_type(column, schema)
            
            # Determine if field is system/editable
            is_system_col = col_name in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
            is_editable = not is_system_col and col_name != 'id'
            is_required = 'NOT NULL' in column.get('constraints', [])
            
            # Build column properties
            props = {
                'is_system_col': is_system_col,
                'is_user_key': col_name in ['note_name', 'contact_name', 'name'] and is_required,
                'is_required': is_required,
                'is_visible': True,
                'is_editable': is_editable,
                'is_clickable': 'url' in col_name.lower(),
                'datatype': 'text',  # Simplify to text for now
                'form_column': form_col,
                'widget_type': widget_type,
                'label_text': self._format_label(col_name),
                'tooltip': column.get('description', f'Enter {self._format_label(col_name).lower()}')
            }
            
            column_props[col_name] = props
        
        return {table_name: column_props}
    
    def _determine_widget_type(self, column, schema):
        """Determine appropriate Streamlit widget type for column"""
        col_name = column['name']
        col_type = column['type']
        
        # Check if column has predefined list of values
        lov = schema.get('list_of_values', {})
        if col_name in lov:
            return 'selectbox'
        
        # Check for common patterns
        if 'note' in col_name.lower() and col_name != 'note_name':
            return 'text_area'
        elif 'description' in col_name.lower():
            return 'text_area'
        elif col_name.endswith('_type') or col_name.endswith('_status'):
            return 'selectbox'
        elif 'date' in col_name.lower():
            return 'date_input'
        else:
            return 'text_input'
    
    def _format_label(self, column_name):
        """Format column name as human-readable label"""
        # Handle common patterns
        label = column_name.replace('_', ' ').title()
        
        # Special cases
        replacements = {
            'Url': 'URL',
            'Id': 'ID',
            'Api': 'API',
            'Ai': 'AI',
            'Note Name': 'Name',
            'Contact Name': 'Name'
        }
        
        for old, new in replacements.items():
            label = label.replace(old, new)
        
        return label
    
    def update_ui_layout_file(self, table_name):
        """
        Update the ui_layout.py file with new COLUMN_PROPS for the table
        """
        ui_layout_file = src_dir / "ui_layout.py"
        column_props = self.generate_column_props(table_name)
        
        # Read existing file
        with open(ui_layout_file, 'r') as f:
            content = f.read()
        
        # Find the COLUMN_PROPS dictionary and add new table
        # This is a simplified approach - in practice, you might want more sophisticated parsing
        
        # For now, just print the generated props so they can be manually added
        print(f"\n📝 Generated COLUMN_PROPS for {table_name}:")
        print("Add this to your ui_layout.py file:")
        print("-" * 50)
        print(f"'{table_name}': {json.dumps(column_props[table_name], indent=4)}")
        print("-" * 50)
        
        return column_props
    
    def generate_sql_ddl(self, table_name):
        """Generate SQL DDL from schema definition"""
        schema = self.load_schema(table_name)
        
        ddl_lines = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
        
        for i, column in enumerate(schema['columns']):
            col_name = column['name']
            col_type = column['type']
            constraints = column.get('constraints', [])
            
            line = f"    {col_name} {col_type}"
            if constraints:
                line += " " + " ".join(constraints)
            
            if i < len(schema['columns']) - 1:
                line += ","
            
            ddl_lines.append(line)
        
        ddl_lines.append(");")
        
        return "\n".join(ddl_lines)
    
    def list_available_schemas(self):
        """List all available schema files"""
        schemas = []
        for schema_file in self.schemas_dir.glob("*.json"):
            table_name = schema_file.stem
            try:
                schema = self.load_schema(table_name)
                schemas.append({
                    'table_name': table_name,
                    'display_name': schema.get('display_name', table_name),
                    'description': schema.get('description', ''),
                    'icon': schema.get('icon', '📄')
                })
            except Exception as e:
                print(f"⚠️ Error loading schema {table_name}: {e}")
        
        return schemas


def main():
    """Command-line interface for page generation"""
    generator = StreamlitPageGenerator()
    
    if len(sys.argv) < 2:
        print("🛠️ Streamlit Tools - Page Generator")
        print("\nUsage:")
        print("  python page_generator.py <command> [args]")
        print("\nCommands:")
        print("  list                    - List available schemas")
        print("  generate <table_name>   - Generate page for table")
        print("  ddl <table_name>        - Generate SQL DDL for table")
        print("  props <table_name>      - Generate COLUMN_PROPS for table")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        schemas = generator.list_available_schemas()
        print("\n📋 Available Schemas:")
        print("-" * 50)
        for schema in schemas:
            print(f"{schema['icon']} {schema['display_name']} ({schema['table_name']})")
            if schema['description']:
                print(f"   {schema['description']}")
        print("-" * 50)
    
    elif command == "generate" and len(sys.argv) > 2:
        table_name = sys.argv[2]
        try:
            output_file = generator.generate_page(table_name)
            print(f"\n🎉 Page generated successfully!")
            print(f"📁 File: {output_file}")
            print(f"🔗 Add to Streamlit menu by restarting the app")
        except Exception as e:
            print(f"❌ Error generating page: {e}")
    
    elif command == "ddl" and len(sys.argv) > 2:
        table_name = sys.argv[2]
        try:
            ddl = generator.generate_sql_ddl(table_name)
            print(f"\n📝 SQL DDL for {table_name}:")
            print("-" * 50)
            print(ddl)
            print("-" * 50)
        except Exception as e:
            print(f"❌ Error generating DDL: {e}")
    
    elif command == "props" and len(sys.argv) > 2:
        table_name = sys.argv[2]
        try:
            generator.update_ui_layout_file(table_name)
        except Exception as e:
            print(f"❌ Error generating COLUMN_PROPS: {e}")
    
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    main()