# this dict config UI layout for form-view
COLUMN_PROPS = {

't_note': {
    # Col_1
    'note_name': {
        'is_system_col': False,
        'is_user_key': True,
        'is_required': True,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_1-1',
        'widget_type': 'text_input',
        'label_text': 'Name'
    },
    'note': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_1-2',
        'widget_type': 'text_area',
        'label_text': 'Description'
    },
    'note_type': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_1-3',
        'widget_type': 'selectbox',
        'label_text': 'Type'
    },

    # Col_2
    'url': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': True,
        'datatype': 'text',
        'form_column': 'COL_2-1',
        'widget_type': 'text_input',
        'label_text': 'URL',
        'tooltip': 'Store YouTube link or primary URL reference'
    },
    'url2': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': True,
        'datatype': 'text',
        'form_column': 'COL_2-2',
        'widget_type': 'text_input',
        'label_text': 'URL2',
        'tooltip': 'Store GitHub link or secondary URL reference'
    },
    'url3': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': True,
        'datatype': 'text',
        'form_column': 'COL_2-3',
        'widget_type': 'text_input',
        'label_text': 'URL3',
        'tooltip': 'Store documentation link or additional reference'
    },
    'note_status': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_2-4',
        'widget_type': 'selectbox',
        'label_text': 'Status'
    },
    # Col_3
    'tags': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': True,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_3-1',
        'widget_type': 'text_input',
        'label_text': 'Tags',
        'tooltip': 'Enter tags separated by commas or spaces (e.g., "ai, python, streamlit")'
    },
    'updated_at': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': True,
        'is_editable': False,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_3-4',
        'widget_type': 'text_input',
        'label_text': 'Timestamp'
    },
    'created_by': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': True,
        'is_visible': True,
        'is_editable': False,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_3-3',
        'widget_type': 'text_input',
        'label_text': 'UserID'
    },
    'is_active': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': False,
        'is_visible': False,
        'is_editable': True,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_3-4',
        'widget_type': 'selectbox',
        'label_text': 'Active?'
    },
    'id': {
        'is_system_col': True,
        'is_user_key': False,
        'is_required': True,
        'is_visible': True,
        'is_editable': False,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_3-5',
        'widget_type': 'text_input',
        'label_text': 'ID'
    },
    'updated_by': {
        'is_system_col': False,
        'is_user_key': False,
        'is_required': True,
        'is_visible': False,
        'is_editable': False,
        'is_clickable': False,
        'datatype': 'text',
        'form_column': 'COL_2-6',
        'widget_type': 'text_input',
        'label_text': 'UserID'
    },
   
}, 

}