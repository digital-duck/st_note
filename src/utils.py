"""
# ToDo

# Done
"""

# basic libs
from datetime import datetime
from io import StringIO 
import os
import re
import shutil
from glob import glob
from traceback import format_exc
from pathlib import Path
from uuid import uuid4
import json
import jsonlines
from time import time

import click   # CLI interface
import getpass
import socket
import os


# special libs
from bs4 import BeautifulSoup
from lxml import html
import pandas as pd
import sqlite3

# streamlit libs
import streamlit as st
from streamlit_option_menu import option_menu
from st_aggrid import (
    AgGrid, GridOptionsBuilder, GridUpdateMode
    , JsCode, DataReturnMode
)

# semantic search libs
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from ui_layout import *


import logging

# Configure the logging system
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / "st_note.log"
if not log_path.exists():
    with open(log_path, 'w'):
        pass

def get_user_id():
    """Return tuple of (username, hostname) - cross-platform"""
    try:
        user_name = getpass.getuser()
    except:
        user_name = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))

    try:
        user_node = socket.gethostname()
    except:
        user_node = 'unknown'

    return f"{user_name}@{user_node}"

#############################
# Config params (1st)
#############################
CURRENT_USER = get_user_id()

DEFAULT_DB_DIALECT = "sqlite"

BLANK_STR_VALUE = ""   # place-holder blank LOV value

STR_APP_NAME             = "Note📝"
STR_MENU_NOTE            = "Take Notes"

STR_SAVE = "✅ Save" # 💾

DB_PATH_SQLITE = "db/notes.sqlite3"

CFG = {
    "DEBUG_FLAG" : False, # True, # 
    "SQL_EXECUTION_FLAG" : True, #  False, #   control SQL
    
    "META_DB_URL" : "./db/notes.sqlite3",
    "META_DB_DDL" : "./schema/tables_ddl.sql",

    # assign table names
    "TABLE_NOTE" : "t_note",            # User Notes

    "NOTE_TYPE": [BLANK_STR_VALUE, 'log', 'learning', 'research', 'project', 'task',  'person', 'organization', 'community',  'event', 'meeting', 'application', 'startup', 'others'],
    "STATUS_CODE": [BLANK_STR_VALUE, "ToDo","WIP", "Done", "Blocked", "Descoped", "Others"],

    # semantic search config
    "EMBEDDING_MODELS": {
        "English (Fast)": "all-MiniLM-L6-v2",
        "Multilingual": "paraphrase-multilingual-MiniLM-L12-v2"
    },
    "DEFAULT_EMBEDDING_MODEL": "English (Fast)",
    "FAISS_INDEX_PATH": "./db/notes_faiss_{model}.index",

    "TEXT_AREA_HEIGHT": 100,
}


# define options for selectbox column type, keyed on column name
BI_STATES = ["Y", BLANK_STR_VALUE, ]   # add empty-str as placeholder
TRI_STATES = ["Y", BLANK_STR_VALUE, None,]

SELECTBOX_OPTIONS = {
    "is_active": [0,1],
    "note_type": CFG["NOTE_TYPE"],
    "note_status": CFG["STATUS_CODE"],
    # Contact management options
    "relationship_type": [BLANK_STR_VALUE, "colleague", "client", "mentor", "vendor", "partner", "prospect", "others"],
    "contact_status": [BLANK_STR_VALUE, "active", "inactive", "prospect", "archived"],
}


logging.basicConfig(
    level=logging.DEBUG if CFG["DEBUG_FLAG"] else logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_path  # Optional: write to a file instead of console
)


def fix_None_val(v):
    return "" if v is None else v

#############################
#  DB related  (2nd)
#############################
class DBConn(object):
    def __init__(self, db_file=CFG["META_DB_URL"]):
        self.conn = sqlite3.connect(db_file)

    def __enter__(self):
        return self.conn

    def __exit__(self, type, value, traceback):
        self.conn.close()

class DBUtils():
    """SQLite database query utility """

    def get_db_connection(self, file_db=CFG["META_DB_URL"]):
        if not file_db.exists():
            raise(f"DB file not found: {file_db}")
        return sqlite3.connect(file_db)

    def run_sql(self, sql_stmt, conn=None, DEBUG_SQL=CFG["DEBUG_FLAG"]):
        """helper to run SQL statement
        """
        if not sql_stmt:
            return
        
        debug_print(f"[DEBUG] {sql_stmt}")
        if conn is None:
            # create new connection
            with DBConn() as _conn:

                if sql_stmt.lower().strip().startswith("select"):
                    return pd.read_sql(sql_stmt, _conn)
                        
                cur = _conn.cursor()
                cur.executescript(sql_stmt)
                _conn.commit()
                return
            
        else:
            # use existing connection
            _conn = conn
            if sql_stmt.lower().strip().startswith("select"):
                return pd.read_sql(sql_stmt, _conn)
                    
            cur = _conn.cursor()
            cur.executescript(sql_stmt)
            _conn.commit()
            return



def strip_brackets(ddl):
    """
    This function removes square brackets from table and column names in a DDL script.
    
    Args:
        ddl (str): The DDL script containing square brackets.
    
    Returns:
        str: The DDL script with square brackets removed.
    """
    # Use regular expressions to match and replace square brackets
    pattern = r"\[([^\]]+)]"  # Match any character except ] within square brackets
    return re.sub(pattern, r"\1", ddl)        

def load_jsonl(file_path):
    if not file_path.exists():
        return
    
    chats = []
    with jsonlines.open(file_path) as reader:
        for obj in reader:
            chats.append(obj)
        st.session_state["my_results"] = chats

def dump_jsonl(file_path):
    if "my_results" not in st.session_state:
        return 
    
    with jsonlines.open(file_path, mode='w') as writer:
        for obj in st.session_state["my_results"]:
            writer.write(obj)  

def trim_str_col_val(data):
    data_new = {}
    for k,v in data.items():
        if isinstance(v, str):
            v = v.strip()
        data_new.update({k:v})
    return data_new

def list_datasets(db_type=DEFAULT_DB_DIALECT):
    """
    traverse subfolder to get all dataset files

    Returns:
        dict of datasets
    """
    sufix = db_type.lower()
    datasets = {}
    cwd = os.getcwd()
    for p in [i for i in glob(f"store/sql/**/*.{sufix}*", recursive=True) if META_APP_NAME not in i and sufix in i.lower()]:
        db_url = os.path.abspath(os.path.join(cwd, p))
        l = Path(db_url).parts
        db_name = l[l.index("sql")+2]
        datasets[db_name] = dict(db_type=db_type, db_url=db_url)
    return datasets

#############################
#  DB Helpers
#############################
def db_run_sql(sql_stmt, conn=None, debug=CFG["DEBUG_FLAG"]):
    """handles both select and insert/update/delete
    """
    if not sql_stmt or conn is None:
        return None
    
    debug_print(sql_stmt, debug=debug)

    x = sql_stmt.lower().strip()
    if x.startswith("select") or x.startswith("with"):
        return pd.read_sql(sql_stmt, conn)
    
    cur = conn.cursor()
    cur.executescript(sql_stmt)
    conn.commit()
    # conn.close()
    return None


def db_execute(sql_stmt, 
               debug=CFG["DEBUG_FLAG"], 
               execute_flag=CFG["SQL_EXECUTION_FLAG"],):
    """handles insert/update/delete
    """
    with DBConn() as _conn:
        debug_print(sql_stmt, debug=debug)
        if execute_flag:
            _conn.execute(sql_stmt)
            _conn.commit()
        else:
            logging.warning("[WARN] SQL Execution is off ! ")   

def db_list_tables_sqlite(db_url):
    """get a list of tables from SQLite database
    """
    with DBConn(db_url) as _conn:
        sql_stmt = f'''
        SELECT 
            name
        FROM 
            sqlite_schema
        WHERE 
            type ='table' AND 
            name NOT LIKE 'sqlite_%';
        '''
        df = pd.read_sql(sql_stmt, _conn)
    return df["name"].to_list()


def db_get_row_count(table_name):
    with DBConn() as _conn:
        sql_stmt = f"""
            select count(*)
            from {table_name};
        """
        df = pd.read_sql(sql_stmt, _conn)
        return df.iat[0,0]

def db_select_by_id(table_name, id_value=""):
    """Select row by primary key: id
    """
    if not id_value: return []

    with DBConn() as _conn:
        sql_stmt = f"""
            select *
            from {table_name} 
            where id = '{id_value}' ;
        """
        return pd.read_sql(sql_stmt, _conn).fillna("").to_dict('records')


def db_upsert(data, user_key_cols="note_name", call_meta_func=False):
    """ 
    """
    if not data: 
        return None

    table_name = data.get("table_name", "")
    if not table_name:
        raise Exception(f"[ERROR] Missing table_name: {data}")
    
    # build SQL
    if call_meta_func:
        visible_columns = get_columns(table_name, prop_name="is_visible")
    else:
        # temp workaround
        visible_columns = get_all_columns(table_name)


    data = trim_str_col_val(data)

    sql_type = "INSERT"
    uk_val = data.get(user_key_cols, "")
    if not uk_val:
        return

    with DBConn() as _conn:
        uk_val = escape_single_quote(uk_val)
        sql_stmt = f"""
            select *
            from {table_name} 
            where {user_key_cols} = '{uk_val}';
        """
        rows = pd.read_sql(sql_stmt, _conn).to_dict('records')

        if len(rows):
            sql_type = "UPDATE"  
            old_row = rows[0]
            id = old_row.get("id")         
           
    upsert_sql = ""
    if sql_type == "INSERT":
        col_clause = []
        val_clause = []
        for col,val in data.items():
            if col not in visible_columns:
                continue
            col_clause.append(col)
            col_val = escape_single_quote(val)
            val_clause.append(f"'{col_val}'")

        upsert_sql = f"""
            insert into {table_name} (
                {", ".join(col_clause)}
            )
            values (
                {", ".join(val_clause)}
            )  
            ;
        """

    else:
        set_clause = []
        for col in visible_columns:

            if col == "is_active":
                val = data.get(col, 1)
                old_val = old_row.get(col, 1)
                if old_val is None:
                    old_val = ""
            else:
                val = data.get(col, "")
                old_val = old_row.get(col, "")

            if isinstance(val, str):
                val = val.strip()
            if (val and old_val and val == old_val) or (not val and not old_val):
                continue

            col_val = escape_single_quote(val)
            set_clause.append(f" {col} = '{col_val}'")

        if set_clause:
            upsert_sql = f"""
                update {table_name} 
                set 
                    {", ".join(set_clause)}
                where id = {id};
            """

    if upsert_sql:
        try:
            with DBConn() as _conn:
                db_run_sql(upsert_sql, _conn)
        except Exception as ex:
            logging.error(f"[ERROR] db_upsert():\n\t{str(ex)}")

def db_query_data(db_url, table_name, limit=50, order_by=""):
    with DBConn(db_url) as _conn:
        order_by = order_by.strip()
        order_by_clause = f" order by {order_by} " if order_by else " "
        limit_clause = f" limit {limit} " if limit and limit > 0 else " "

        sql_stmt = f"""
            select 
                *
            from {table_name}
            {order_by_clause}
            {limit_clause}
            ;
        """
        return pd.read_sql(sql_stmt, _conn)


def db_delete_by_id(data):
    if not data: 
        return None
    
    table_name = data.get("table_name", "")
    if not table_name:
        raise Exception(f"[ERROR] Missing table_name: {data}")

    id_val = data.get("id")
    if not id_val:
        return None
    
    delete_sql = f"""
        delete from {table_name}
        where id = {id_val};
    """
    with DBConn() as _conn:
        db_run_sql(delete_sql, _conn)


def db_update_by_id(data, update_changed=True):
    if not data: 
        return
    
    table_name = data.get("table_name", "")
    if not table_name:
        raise Exception(f"[ERROR] Missing table_name: {data}")

    id_val = data.get("id")
    if not id_val:
        return

    if update_changed:
        rows = db_select_by_id(table_name=table_name, id_value=id_val)
        if len(rows) < 1:
            return
        old_row = rows[0]

    editable_columns = get_columns(table_name, prop_name="is_editable")

    # build SQL
    set_clause = []
    for col,val in data.items():
        if col not in (editable_columns + ["updated_by"]): 
            continue

        if update_changed:
            # skip if no change
            old_val = old_row.get(col, "")
            if val != old_val:
                set_clause.append(f"{col} = '{escape_single_quote(val)}'")
        else:
            set_clause.append(f"{col} = '{escape_single_quote(val)}'")

    if set_clause:
        update_sql = f"""
            update {table_name}
            set {', '.join(set_clause)}
            where id = {id_val};
        """
        with DBConn() as _conn:
            db_run_sql(update_sql, _conn)

#############################
#  Misc Helpers
#############################
def debug_print(msg, debug=CFG["DEBUG_FLAG"]):
    if msg:
        # st.write(f"[DEBUG] {str(msg)}")
        print(f"[DEBUG] {str(msg)}")
        # logging.debug(f"[DEBUG] {str(msg)}")

def convert_df2csv(df, index=True):
    return df.to_csv(index=index).encode('utf-8')

def convert_htm2txt(html_txt):
    return html.fromstring(html_txt).text_content().strip()

def is_noise_word(html_txt):
    return convert_htm2txt(html_txt) in CFG["NOISE_WORDS"]

def parse_bot_ver(bot_ver, sep="__"):
    return [x.strip() for x in bot_ver.split(sep) if x.strip()]

def parse_html_txt_claude(html_txt):
    """
    Extract question/answer from HTML text

    Returns:
        list of dialog content
    """
    cells = []
    if not html_txt: return cells

    soup = BeautifulSoup(html_txt, "html.parser")
    results=soup.findAll("div", class_="contents")
    for i in range(len(results)):
        v = results[i].prettify()
        if is_noise_word(v): continue
        # important to preserve HTML string because python code snippets are formatted
        cells.append(v)
    return cells

def escape_single_quote(s):
    if s is None or s == 'None':
        return ''
    if not "'" in s:
        return s
    return s.strip().replace("\'", "\'\'")

def list2sql_str(l):
    """convert a list into SQL in string
    """
    return str(l).replace("[", "(").replace("]", ")")

def get_uid():
    return os.getlogin()

def get_ts_now():
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

def get_uuid():
    return str(uuid4())

#############################
#  UI related
#############################
# Aggrid options
# how to set column width
# https://stackoverflow.com/questions/72624323/how-to-set-a-max-column-length-for-streamlit-aggrid
AGGRID_OPTIONS = {
    "paginationPageSize": 10,
    "grid_height": 370,
    "return_mode_value": DataReturnMode.__members__["FILTERED"],
    "update_mode_value": GridUpdateMode.__members__["MODEL_CHANGED"],
    "fit_columns_on_grid_load": True,
    "selection_mode": "single",  #  "multiple",  # 
    "allow_unsafe_jscode": True,
    "groupSelectsChildren": True,
    "groupSelectsFiltered": True,
    "enable_pagination": True,
}

# list of system columns in all tables
SYS_COLS = ["id","created_at","updated_at","created_by","updated_by","is_active"]

# column UI-properties
PROPS = [
    'is_system_col',
    'is_user_key',
    'is_required',
    'is_visible',
    'is_editable',
    'is_clickable',
    'form_column',
    'widget_type',
    'label_text',
    'kwargs',
    'tooltip'
]



def map_streamlit_widget_type(col_name, data_type):
    if data_type in ("real", "integer"):
        return "number_input"
    else:
        if (col_name.startswith("is_") or col_name.startswith("has_") or col_name.startswith("as_")):
            return "selectbox"
        else:
            return "text_input"

def init_cap(col_name):
    return " ".join([c.capitalize() for c in col_name.split("_")])

def parse_ddl_reserved(x):
    x = x.strip()
    for kw in ["--", "primary ", "not ", "default "]:
        if kw in x: 
            x = x.split(kw)[0].strip()
    return x

def parse_ddl_line(line):
    """handle , and --, returns a list of column definition
    """
    res = []
    x = line.strip()
    if x.startswith("--"):
        return res
    
    for j in [i.strip() for i in x.split(",") if i.strip()]:
        j = parse_ddl_reserved(j)
        if j:
            res.append(j)
    return res

def parse_ddl(ddl_str, filtered_types=[]):
    """Parse DDL text string into col_datatype map
    
    filtered_types = []: return all, else only specified types
    """
    out = []
    for i in ddl_str.lower().split("create "):
        if not i.startswith("table "): continue 
        out.append(i.split("\n"))
        
    # table_names = []
    col_datatypes = {}
    for t in out:
        if "table" in t[0]:
            table_name = t[0].split()[-1]
        # table_names.append(table_name)
        else:
            logging.error(f"[ERROR] Table name not found: {t}")
            continue
            
        t2 = t[1:]
        i_st = i_sp = -2
        for i in range(len(t2)):
            x = t2[i].strip()
            if x.startswith("("):
                i_st = i
            elif x.startswith(")"):
                i_sp = i
        if i_st == -2 or i_sp == -2:
            logging.error(f"[ERROR] Missing parathesis: {t2}")
            continue 

        t3 = []
        for i in t2[i_st+1:i_sp]:
            line = i.strip()
            res = parse_ddl_line(line)
            if res: 
                t3.extend(res)

        m = {}
        for x in t3:
            y = x.strip().split()
            if len(y) == 0: 
                continue
            col_name = y[0]
            datatype = "text" if len(y) < 2 else y[1]
            if not filtered_types or datatype in filtered_types:
                m[col_name] = datatype
                
        col_datatypes[table_name] = m
    
    return col_datatypes

def prepare_column_props(col_defn):
    """Prepare UI config
    """
    col_props = {}
    for table_name in col_defn.keys():
        col_types = col_defn[table_name]
        col_props[table_name] = {}
        for col_name, data_type in col_types.items():
            widget_type = map_streamlit_widget_type(col_name, data_type)
            label_text = init_cap(col_name)
            col_props[table_name].update({
                col_name : dict(
                    is_system_col=False,
                    is_user_key=False,
                    is_required=False,
                    is_visible=True,
                    is_editable=True,
                    is_clickable=False,
                    datatype=data_type,
                    form_column="COL_1-1",
                    widget_type=widget_type,
                    label_text=label_text,
                )})
    return col_props

def gen_label(col):
    "Convert table column into form label"
    if col == 'ts_created': return "Created At"
    if "_" not in col:
        if col.upper() in ["URL","ID"]:
            return col.upper()
        elif col.upper() == "TS":
            return "Timestamp"
        return col.capitalize()

    cols = []
    for c in col.split("_"):
        c  = c.strip()
        if not c: continue
        cols.append(c.capitalize())
    return " ".join(cols)



def get_all_columns(table_name):
    cols = COLUMN_PROPS[table_name].keys()
    out = [c.split()[0] for c in cols]
    return out

def get_columns(table_name, prop_name="is_visible"):
    cols_bool = []
    cols_text = {}
    for k,v in COLUMN_PROPS[table_name].items():
        if prop_name.startswith("is_") and v.get(prop_name, False):
            cols_bool.append(k)
            
        if not prop_name.startswith("is_"):
            val = v.get(prop_name, "")
            if val:
                cols_text.update({k: val})
    
    return cols_bool or cols_text

def parse_column_props():
    """parse COLUMN_PROPS map
    """
    col_defs = {}
    for table_name in COLUMN_PROPS.keys():
        defs = {}
        cols_widget_type = {}
        cols_label_text = {}
        for p in PROPS:
            res = get_columns(table_name, prop_name=p)
            if p == 'widget_type':
                cols_widget_type = res
            elif p == 'label_text':
                cols_label_text = res
            defs[p] = res
            
        # reset label
        for col in cols_widget_type.keys():
            label = cols_label_text.get(col, "")
            if not label:
                label = gen_label(col)
            cols_label_text.update({col : label})
        defs['label_text'] = cols_label_text
        defs['all_columns'] = list(cols_widget_type.keys())

        # sort form_column alpha-numerically
        # max number of form columns = 3
        # add them
        tmp = {}
        for i in range(1,4):
            m = {k:v for k,v in defs['form_column'].items() if v.startswith(f"col{i}-")}
            tmp[f"col{str(i)}_columns"] = sorted(m, key=m.__getitem__)        
        defs.update(tmp)
        col_defs[table_name] = defs
        
    return col_defs

def ui_layout_form_fields(data,form_name,old_row,col,
                        widget_types,col_labels,system_columns,col_tooltips=None):
    DISABLED = col in system_columns
    key_name_field = f"col_{form_name}_{col}"
    tooltip = col_tooltips.get(col, "") if col_tooltips else ""
    if old_row:
        old_val = old_row.get(col, "")
        widget_type = widget_types.get(col, "text_input")
        if widget_type == "text_area":
            kwargs = {"height": CFG["TEXT_AREA_HEIGHT"]}
            val = st.text_area(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field, help=tooltip, **kwargs)
        elif widget_type == "date_input":
            old_date_input = old_val.split("T")[0]
            if old_date_input:
                val_date = datetime.strptime(old_date_input, "%Y-%m-%d")
            else:
                val_date = datetime.now().date()
            val = st.date_input(col_labels.get(col), value=val_date, disabled=DISABLED, key=key_name_field, help=tooltip)
            val = datetime.strftime(val, "%Y-%m-%d")
        elif widget_type == "time_input":
            old_time_input = old_val
            if old_time_input:
                val_time = datetime.strptime(old_time_input.split(".")[0], "%H:%M:%S").time()
            else:
                val_time = datetime.now().time()
            val = st.time_input(col_labels.get(col), value=val_time, disabled=DISABLED, key=key_name_field, help=tooltip)
        elif widget_type == "selectbox":
            # check if options is avail, otherwise display as text_input
            if col in SELECTBOX_OPTIONS:
                try:
                    _options = SELECTBOX_OPTIONS.get(col,[])
                    old_val = old_row.get(col, BLANK_STR_VALUE)
                    _idx = _options.index(old_val)
                    val = st.selectbox(col_labels.get(col), _options, index=_idx, key=key_name_field, help=tooltip)
                except ValueError:
                    val = old_row.get(col, "")
            else:
                val = st.text_input(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field, help=tooltip)
        elif widget_type == "multiselect":
            # check if options is avail, otherwise display as text_input
            if col in SELECTBOX_OPTIONS:
                try:
                    _options = SELECTBOX_OPTIONS.get(col,[])
                    old_val = old_row.get(col, BLANK_STR_VALUE).split(",")
                    val = st.multiselect(col_labels.get(col), _options, default=old_val, key=key_name_field, help=tooltip)
                except ValueError:
                    val = old_row.get(col, "")
            else:
                val = st.text_input(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field, help=tooltip)

        else:
            val = st.text_input(col_labels.get(col), value=old_val, disabled=DISABLED, key=key_name_field, help=tooltip)

        if val != old_val:
            data.update({col : val})

    return data


def ui_layout_form(selected_row, table_name):

    form_name = table_name
    COLUMN_DEFS = parse_column_props()
    COL_DEFS = COLUMN_DEFS[table_name]
    visible_columns = COL_DEFS["is_visible"]
    system_columns = COL_DEFS["is_system_col"]
    form_columns = COL_DEFS["form_column"]
    col_labels = COL_DEFS["label_text"]
    widget_types = COL_DEFS["widget_type"]
    col_tooltips = COL_DEFS.get("tooltip", {})

    old_row = {}
    for col in visible_columns:
        old_row[col] = selected_row.get(col, "") if selected_row is not None else ""

    data = {
        "table_name": table_name,
        "updated_by": selected_row.get("updated_by", CURRENT_USER) if selected_row else CURRENT_USER,
    }

    # copy id if present
    id_val = old_row.get("id")
    if id_val:
        data.update({"id" : id_val})

    # display form and populate data dict
    col_col = {}
    col_prefix = [f"COL_{n}" for n in range(1,6)]  # max 5 columns
    for pfx in col_prefix:
        col_columns = col_col.get(pfx, [])
        for c in visible_columns:
            if form_columns.get(c, "").startswith(pfx):
                col_columns.append(c)
                col_col[pfx] = col_columns
    N_COLS = len(col_col.keys())

    key_names = []
    with st.form(form_name, clear_on_submit=True):
        st_cols = st.columns(N_COLS)
        id_col = 0
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns,col_tooltips)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Hard-delete Record?", value=False)
                    data.update({col: delete_flag})

        id_col = 1
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns,col_tooltips)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Hard-delete Record?", value=False)
                    data.update({col: delete_flag})

        id_col = 2
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns,col_tooltips)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Hard-delete Record?", value=False)
                    data.update({col: delete_flag})


        id_col = 3
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns,col_tooltips)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Hard-delete Record?", value=False)
                    data.update({col: delete_flag})

        id_col = 4
        if len(st_cols) > id_col:
            with st_cols[id_col]:
                for col in col_col[col_prefix[id_col]]:
                    data = ui_layout_form_fields(data,form_name,old_row,col,
                                widget_types,col_labels,system_columns,col_tooltips)
                    key_names.append(f"col_{form_name}_{col}")

                if id_col == len(st_cols)-1:
                    # add checkbox for deleting this record
                    col = "delelte_record"
                    delete_flag = st.checkbox("Hard-delete Record?", value=False)
                    data.update({col: delete_flag})

        save_btn = st.form_submit_button(STR_SAVE, help="Double-click to save and refresh")  
        if save_btn:
            try:
                # Collect form values from session state
                for key_name in key_names:
                    col_name = key_name.replace(f"col_{form_name}_", "")
                    if col_name in st.session_state:
                        data[col_name] = st.session_state[col_name]
                
                delete_flag = data.get("delelte_record", False)
                data_changed = False
                
                if delete_flag:
                    if data.get("id"):
                        db_delete_by_id(data)
                        data_changed = True
                else:
                    if data.get("id"):
                        data.update({"updated_at": get_ts_now(),
                                    })
                        db_update_by_id(data)
                        data_changed = True
                    else:
                        data.update({
                                    "updated_at": get_ts_now(),
                                    "created_at": get_ts_now(),
                                    "updated_by": CURRENT_USER,
                                    "created_by": CURRENT_USER,
                                    })
                        db_upsert(data)
                        data_changed = True
                
                # Refresh FAISS index after any data change
                if data_changed:
                    try:
                        # Rebuild indices for all available models
                        for model_name in CFG["EMBEDDING_MODELS"].keys():
                            build_faiss_index(model_name)
                        st.success("Note saved and search indices updated!")
                    except Exception as idx_ex:
                        st.warning(f"Note saved but search index update failed: {idx_ex}")
                        logging.error(f"FAISS index refresh failed: {idx_ex}")

            except Exception as ex:
                st.error(f"{str(ex)}")

        # clear form after save (existing logic)
        try:
            if save_btn:  # Only clear after save
                for c in key_names:
                    st.session_state[c] = ""
        except Exception as e:
            pass # ignore

    ### Clear Form does not work
    # # Clear Form button outside the form
    # if st.button("🧹 Clear Form", help="Clear all form fields"):
    #     try:
    #         # Clear all form-related session state keys for this table
    #         form_prefix = f"col_{form_name}_"
    #         keys_to_clear = [key for key in st.session_state.keys() if key.startswith(form_prefix)]
    #         for key in keys_to_clear:
    #             del st.session_state[key]
    #         st.success("Form cleared!")
    #         st.rerun()
    #     except Exception as e:
    #         st.error(f"Error clearing form: {e}")
    #         pass # ignore


def ui_display_df_grid(df, 
        selection_mode="single",  # "multiple", 
        fit_columns_on_grid_load=AGGRID_OPTIONS["fit_columns_on_grid_load"],
        page_size=AGGRID_OPTIONS["paginationPageSize"],
        grid_height=AGGRID_OPTIONS["grid_height"],
        clickable_columns=[],
        editable_columns=[],
        colored_columns={}
    ):
    """show input df in a grid and return selected row
    """

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode,
            use_checkbox=True,
            groupSelectsChildren=AGGRID_OPTIONS["groupSelectsChildren"], 
            groupSelectsFiltered=AGGRID_OPTIONS["groupSelectsFiltered"]
        )
    gb.configure_pagination(paginationAutoPageSize=False, 
        paginationPageSize=page_size)
    
    gb.configure_columns(editable_columns, editable=True)

    # color column
    for k,v in colored_columns.items():
        gb.configure_column(k, cellStyle=v)

    if clickable_columns:       # config clickable columns
        # js_code = """
        #     function(params) {return params.value ? `<a href=${params.value} target="_blank">${params.value}</a>` : "" }
        # """
        # fix
        cell_renderer_url =  JsCode("""
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('a');
                    this.eGui.innerText = params.value;
                    this.eGui.setAttribute('href', params.value);
                    this.eGui.setAttribute('style', "text-decoration:none");
                    this.eGui.setAttribute('target', "_blank");
                }
                getGui() {
                    return this.eGui;
                }
            }
        """)
        for col_name in clickable_columns:
            gb.configure_column(col_name, cellRenderer=cell_renderer_url)


    gb.configure_grid_options(domLayout='normal')
    grid_response = AgGrid(
        df, 
        gridOptions=gb.build(),
        data_return_mode=AGGRID_OPTIONS["return_mode_value"],
        update_mode=AGGRID_OPTIONS["update_mode_value"],
        height=grid_height, 
        # width='100%',
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
    )
 
    return grid_response

def df_to_csv(df, index=False):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=index).encode('utf-8')

def format_insert_sql(out_dict, table_name="w_zi_dup_merged"):
    """create SQL Insert statement using out_dict data
    """
    col_list = []
    val_list = []

    for k,v in out_dict.items():
        col_list.append(k)
        try:
            x = float(v)
            val_list.append(str(v)) 
        except:
            v = escape_single_quote(v)
            val_list.append(f"'{v}'") 

    col_str = ", ".join(col_list)
    val_str = ", ".join(val_list)
    sql_insert = f"""
        insert into {table_name} ({col_str}) 
        values ({val_str});
    """
    return sql_insert

def strip_null(data):
    data_new = []
    for d in data: 
        if isinstance(d,str):
            d = d.strip()
            if d: data_new.append(d)
            continue 
        data_new.append(d)
    return data_new 

def merge_data_col(data, sep = " / "):
    """ concat unique non-blank values
    """
    return sep.join(set(strip_null(data)))

def merge_single_col(data):
    """pick a single non-blank value
    https://stackoverflow.com/questions/59825/how-to-retrieve-an-element-from-a-set-without-removing-it
    """
    ds = set(strip_null(data))
    if not ds: return ""
    for d in ds:
        break
    return d


def gen_markdown_text(data, keys=["llm_vendor","llm_model","vector_db","db_type","db_name","db_url"]):
    table = "| Param | Value |\n|-----|-------|\n"
    table += "\n".join([f"| {k} | {v} |" for k,v in data.items() if k in keys])
    return table

def cfg_show_data(data):
    config_table_md = gen_markdown_text(data)
    st.markdown(config_table_md, unsafe_allow_html=True) 

def snake_case(s):
    """Convert string to snake_case."""
    # Replace any non-word character with underscore
    s = re.sub(r'[^\w\s]', '_', s)
    # Replace whitespace with underscore
    s = re.sub(r'\s+', '_', s)
    # Convert to lowercase
    return s.lower()

@click.command()
@click.option(
    '--input-dir', '-i',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default='.',
    help='Directory containing CSV files (default: current directory)'
)
@click.option(
    '--output', '-o',
    type=click.Path(dir_okay=False),
    default='combined_data.xlsx',
    help='Output Excel file name (default: combined_data.xlsx)'
)
@click.option(
    '--trim-prefix', '-t',
    type=click.STRING,
    default='',
    help='trim CSV filename with prefix avoiding 32 chars sheetname limitation'
)
def convert_csvs_to_excel(input_dir, output, trim_prefix):
    """
    Convert all CSV files in the specified directory to sheets in a single Excel file.
    Each CSV becomes a sheet named after the original file.
    """
    # Excel has a 31 character limit for sheet names
    MAX_SHEETNAME = 32 - 1
    trim_prefix = snake_case(trim_prefix)

    # Ensure output has .xlsx extension
    if not output.lower().endswith('.xlsx'):
        output += '.xlsx'
    
    try:
        # Get all CSV files in the directory
        csv_files = glob(f"{input_dir}/*.csv")
        
        if not csv_files:
            click.echo("No CSV files found in the specified directory.", err=True)
            return
        
        # Process each CSV file
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            with click.progressbar(csv_files, label='Processing CSV files') as files:
                for csv_path in files:
                    # Read the CSV file
                    df = pd.read_csv(csv_path)
                    
                    # Create sheet name from file name (remove .csv extension)
                    orig_csv_name = Path(csv_path).stem
                    logging.info(f"\nProcessing {csv_path} ...")
                    sheet_name = snake_case(orig_csv_name)

                    if sheet_name.startswith(trim_prefix):
                        sheet_name = sheet_name.replace(trim_prefix, "")

                    # remove extra '_'
                    sheet_name = "_".join([i for i in sheet_name.split("_") if i])

                    if len(sheet_name) > MAX_SHEETNAME:
                        sheet_name = sheet_name[:MAX_SHEETNAME]
                        click.echo(f"Warning: Sheet name '{orig_csv_name}' truncated to '{sheet_name}'")
                    
                    # Write the dataframe to Excel sheet
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        click.echo(f"\nSuccess! Created {output} with {len(csv_files)} sheets.")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

def parse_id_list(ids):
    """split list of ID string into list
    """
    x = ids.replace(",", " ").replace(";", " ")
    return [i.strip() for i in x.split() if i.strip()]


def snake_case(s):
    """Convert string to snake_case."""
    # Replace spaces and special chars with underscore
    s = re.sub(r'[^a-zA-Z0-9]', '_', s)
    # Convert camelCase to snake_case
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    # Convert to lowercase and remove multiple underscores
    return re.sub('_+', '_', s.lower()).strip('_')



def prepend_chat_history(chat_history, question):
    """ Add past N chats to question as new prompt
    """
    if not chat_history:
        return question

    contents = []    
    for i in chat_history:
        if i.get("role") == "user":
            contents.append("\n User: " + i.get("content", "") + " \n")
        if i.get("role") == "assistant":
            contents.append("\n Assistant: " + i.get("content", "") + " \n")

    return "\n".join(contents) + f"\n User: {question} \n\n Assistant: \n"

#############################
#  Semantic Search Functions
#############################

@st.cache_resource
def load_embedding_model(model_name=None):
    """Load and cache the sentence transformer model"""
    if model_name is None:
        model_name = CFG["DEFAULT_EMBEDDING_MODEL"]
    
    model_id = CFG["EMBEDDING_MODELS"].get(model_name, CFG["EMBEDDING_MODELS"][CFG["DEFAULT_EMBEDDING_MODEL"]])
    return SentenceTransformer(model_id)

def get_index_path(model_name=None):
    """Get model-specific FAISS index path"""
    if model_name is None:
        model_name = CFG["DEFAULT_EMBEDDING_MODEL"]
    
    # Create safe filename from model name
    safe_model_name = model_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    return CFG["FAISS_INDEX_PATH"].format(model=safe_model_name)

def combine_note_text(note_name, note, url, url2, url3, local):
    """Combine note fields into a single text for embedding"""
    parts = []
    if note_name and note_name.strip():
        parts.append(f"Title: {note_name.strip()}")
    if note and note.strip():
        parts.append(f"Content: {note.strip()}")
    if url and url.strip():
        parts.append(f"URL: {url.strip()}")
    if url2 and url2.strip():
        parts.append(f"URL: {url2.strip()}")
    if url3 and url3.strip():
        parts.append(f"URL: {url3.strip()}")
    if local and local.strip():
        parts.append(f"URL: {local.strip()}")
    return " | ".join(parts)

def build_faiss_index(model_name=None):
    """Build or rebuild FAISS index from all notes"""
    model = load_embedding_model(model_name)
    
    with DBConn() as _conn:
        sql_stmt = f"""
            SELECT id, note_name, note, url, url2, url3, local
            FROM {CFG['TABLE_NOTE']} 
            WHERE is_active = 1
            ORDER BY id
        """
        df = pd.read_sql(sql_stmt, _conn)
    
    if df.empty:
        return None, []
    
    texts = []
    note_ids = []
    
    for _, row in df.iterrows():
        combined_text = combine_note_text(
            row['note_name'], row['note'], row['url'], row['url2'], row['url3'], row['local']
        )
        texts.append(combined_text)
        note_ids.append(row['id'])
    
    embeddings = model.encode(texts, convert_to_tensor=False)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype('float32'))
    
    index_path = get_index_path(model_name)
    faiss.write_index(index, index_path)
    
    return index, note_ids

def load_faiss_index(model_name=None):
    """Load existing FAISS index"""
    try:
        index_path = get_index_path(model_name)
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            
            with DBConn() as _conn:
                sql_stmt = f"""
                    SELECT id FROM {CFG['TABLE_NOTE']} 
                    WHERE is_active = 1 
                    ORDER BY id
                """
                df = pd.read_sql(sql_stmt, _conn)
                note_ids = df['id'].tolist()
            
            return index, note_ids
        else:
            return build_faiss_index(model_name)
    except Exception as e:
        logging.error(f"Error loading FAISS index: {e}")
        return build_faiss_index(model_name)

def semantic_search(query, top_k=10, score_threshold=0.1, model_name=None):
    """Perform semantic search using FAISS"""
    if not query or not query.strip():
        return []
    
    try:
        model = load_embedding_model(model_name)
        index, note_ids = load_faiss_index(model_name)
        
        if index is None or not note_ids:
            return []
        
        query_embedding = model.encode([query.strip()], convert_to_tensor=False)
        faiss.normalize_L2(query_embedding)
        
        scores, indices = index.search(query_embedding.astype('float32'), min(top_k, len(note_ids)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(note_ids) and score > score_threshold:  # threshold for relevance
                results.append({
                    'note_id': note_ids[idx],
                    'similarity_score': float(score)
                })
        
        return results
    except Exception as e:
        logging.error(f"Error in semantic search: {e}")
        return []

def refresh_faiss_index(show_messages=True, model_name=None):
    """Rebuild FAISS index (call after adding/updating notes)"""
    try:
        build_faiss_index(model_name)
        if show_messages:
            model_display = model_name or CFG["DEFAULT_EMBEDDING_MODEL"]
            st.success(f"Search index updated successfully for {model_display}!")
    except Exception as e:
        if show_messages:
            st.error(f"Error updating search index: {e}")
        logging.error(f"Error refreshing FAISS index: {e}")
        raise e


#############################
# Streamlit Tools Enhanced Functions
# (Added for meta-application support without modifying existing functions)
#############################

def db_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        with DBConn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"Error checking table existence: {e}")
        return False

def db_create_table_from_ddl(ddl_statement):
    """Execute DDL statement to create a table"""
    try:
        with DBConn() as conn:
            cursor = conn.cursor()
            cursor.execute(ddl_statement)
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Error creating table: {e}")
        return False

def db_get_table_columns(table_name):
    """Get column information for a table"""
    try:
        with DBConn() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            return [{"name": col[1], "type": col[2], "not_null": col[3], "default": col[4], "pk": col[5]} 
                   for col in columns]
    except Exception as e:
        logging.error(f"Error getting table columns: {e}")
        return []

def db_generic_search(table_name, search_query="", filters=None, order_by="updated_at DESC"):
    """Generic search function for any table following our conventions"""
    try:
        with DBConn() as conn:
            # Build WHERE clause
            where_conditions = ["is_active = 1"]
            params = []
            
            # Add search query if provided
            if search_query and search_query.strip():
                # Get text columns for search
                columns = db_get_table_columns(table_name)
                text_columns = [col["name"] for col in columns if col["type"].upper() == "TEXT"]
                
                if text_columns:
                    search_conditions = []
                    for col in text_columns:
                        if col not in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                            search_conditions.append(f"{col} LIKE ?")
                            params.append(f"%{search_query.strip()}%")
                    
                    if search_conditions:
                        where_conditions.append(f"({' OR '.join(search_conditions)})")
            
            # Add filters if provided
            if filters:
                for field, values in filters.items():
                    if values:  # Only add filter if values are provided
                        if isinstance(values, list):
                            placeholders = ','.join(['?' for _ in values])
                            where_conditions.append(f"{field} IN ({placeholders})")
                            params.extend(values)
                        else:
                            where_conditions.append(f"{field} = ?")
                            params.append(values)
            
            where_clause = " AND ".join(where_conditions)
            sql = f"SELECT * FROM {table_name} WHERE {where_clause} ORDER BY {order_by}"
            
            return pd.read_sql(sql, conn, params=params)
    
    except Exception as e:
        logging.error(f"Error in generic search: {e}")
        return pd.DataFrame()

def db_generic_upsert(table_name, data, key_fields=None):
    """Generic upsert function for any table"""
    try:
        # Add system fields
        current_time = datetime.now().isoformat()
        
        if 'id' not in data or not data['id']:
            # New record
            data.update({
                'created_at': current_time,
                'updated_at': current_time,
                'created_by': CURRENT_USER,
                'updated_by': CURRENT_USER,
                'is_active': 1
            })
        else:
            # Update existing record
            data.update({
                'updated_at': current_time,
                'updated_by': CURRENT_USER
            })
        
        return db_upsert(table_name, data)
    
    except Exception as e:
        logging.error(f"Error in generic upsert: {e}")
        return False

def get_available_tags_for_table(table_name):
    """Get all unique tags for a table"""
    try:
        with DBConn() as conn:
            sql = f"""
                SELECT DISTINCT tags FROM {table_name} 
                WHERE is_active = 1 AND tags IS NOT NULL AND tags != ''
            """
            df = pd.read_sql(sql, conn)
            
            # Parse and flatten all tags
            all_tags = set()
            for tags_str in df['tags'].dropna():
                if tags_str.strip():
                    # Split by both comma and space, normalize
                    import re
                    tags = re.split(r'[,\s]+', tags_str.strip())
                    for tag in tags:
                        tag = tag.strip().upper()
                        if tag:
                            all_tags.add(tag)
            
            return sorted(list(all_tags))
    
    except Exception as e:
        logging.error(f"Error getting tags for {table_name}: {e}")
        return []

def build_generic_faiss_index(table_name, text_fields, model_name=None):
    """Build FAISS index for any table with specified text fields"""
    try:
        model_name = model_name or CFG["DEFAULT_EMBEDDING_MODEL"]
        model = load_embedding_model(model_name)
        
        with DBConn() as conn:
            # Get text columns for the table
            select_fields = ['id'] + text_fields
            sql = f"""
                SELECT {', '.join(select_fields)} FROM {table_name}
                WHERE is_active = 1
                ORDER BY id
            """
            df = pd.read_sql(sql, conn)
        
        if df.empty:
            logging.info(f"No active records found in {table_name}")
            return None, []
        
        # Combine text fields
        texts = []
        record_ids = []
        
        for _, row in df.iterrows():
            combined_text_parts = []
            for field in text_fields:
                value = str(row.get(field, '') or '')
                if value.strip():
                    combined_text_parts.append(value.strip())
            
            combined_text = ' '.join(combined_text_parts)
            if combined_text.strip():
                texts.append(combined_text)
                record_ids.append(row['id'])
        
        if not texts:
            logging.info(f"No text content found in {table_name}")
            return None, []
        
        # Generate embeddings
        embeddings = model.encode(texts, convert_to_tensor=False, show_progress_bar=False)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))
        
        # Save index
        index_path = CFG["FAISS_INDEX_PATH"].format(model=f"{table_name}_{model_name.replace('/', '_')}")
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        faiss.write_index(index, index_path)
        
        logging.info(f"Built FAISS index for {table_name}: {len(texts)} records")
        return index, record_ids
    
    except Exception as e:
        logging.error(f"Error building FAISS index for {table_name}: {e}")
        return None, []

def generic_semantic_search(table_name, query, text_fields, top_k=10, score_threshold=0.1, model_name=None):
    """Perform semantic search on any table"""
    if not query or not query.strip():
        return []
    
    try:
        model_name = model_name or CFG["DEFAULT_EMBEDDING_MODEL"]
        model = load_embedding_model(model_name)
        
        # Load or build index
        index_path = CFG["FAISS_INDEX_PATH"].format(model=f"{table_name}_{model_name.replace('/', '_')}")
        
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            
            # Get record IDs (rebuild from database)
            with DBConn() as conn:
                sql = f"SELECT id FROM {table_name} WHERE is_active = 1 ORDER BY id"
                df = pd.read_sql(sql, conn)
                record_ids = df['id'].tolist()
        else:
            # Build index if it doesn't exist
            index, record_ids = build_generic_faiss_index(table_name, text_fields, model_name)
            if index is None:
                return []
        
        # Perform search
        query_embedding = model.encode([query.strip()], convert_to_tensor=False)
        faiss.normalize_L2(query_embedding)
        
        scores, indices = index.search(query_embedding.astype('float32'), min(top_k, len(record_ids)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(record_ids) and score > score_threshold:
                results.append({
                    'record_id': record_ids[idx],
                    'similarity_score': float(score)
                })
        
        return results
    
    except Exception as e:
        logging.error(f"Error in semantic search for {table_name}: {e}")
        return []

def perform_hybrid_search(table_name, query, text_fields, filters=None, search_mode="hybrid", top_k=10):
    """
    Perform hybrid search combining keyword and semantic search for any table
    
    Args:
        table_name: Name of the table to search
        query: Search query string
        text_fields: List of text fields to search in
        filters: Dictionary of field filters
        search_mode: "keyword", "semantic", or "hybrid"
        top_k: Maximum number of results
    
    Returns:
        pandas.DataFrame with search results
    """
    try:
        if search_mode == "keyword":
            # Keyword search only
            return db_generic_search(table_name, query, filters)
        
        elif search_mode == "semantic":
            # Semantic search only
            semantic_results = generic_semantic_search(table_name, query, text_fields, top_k)
            if semantic_results:
                record_ids = [r['record_id'] for r in semantic_results]
                with DBConn() as conn:
                    placeholders = ','.join(['?' for _ in record_ids])
                    sql = f"SELECT * FROM {table_name} WHERE id IN ({placeholders}) AND is_active = 1"
                    df = pd.read_sql(sql, conn, params=record_ids)
                
                # Add similarity scores
                score_map = {r['record_id']: r['similarity_score'] for r in semantic_results}
                df['similarity_score'] = df['id'].map(score_map)
                return df.sort_values('similarity_score', ascending=False)
            else:
                return pd.DataFrame()
        
        else:  # hybrid
            # Combine keyword and semantic search
            keyword_results = db_generic_search(table_name, query, filters)
            semantic_results = generic_semantic_search(table_name, query, text_fields, top_k)
            
            if semantic_results:
                semantic_ids = [r['record_id'] for r in semantic_results]
                with DBConn() as conn:
                    placeholders = ','.join(['?' for _ in semantic_ids])
                    sql = f"SELECT * FROM {table_name} WHERE id IN ({placeholders}) AND is_active = 1"
                    semantic_df = pd.read_sql(sql, conn, params=semantic_ids)
                
                # Combine results (union)
                all_results = pd.concat([keyword_results, semantic_df]).drop_duplicates(subset=['id'])
                return all_results.sort_values('updated_at', ascending=False).head(top_k)
            else:
                return keyword_results.head(top_k)
    
    except Exception as e:
        logging.error(f"Error in hybrid search for {table_name}: {e}")
        return pd.DataFrame()


#############################
# Database-Driven UI Configuration Functions
# (Inspired by Siebel Tools - Store UI metadata in database)
#############################

def create_ui_layout_table():
    """Create the t_ui_layout_config table if it doesn't exist"""
    try:
        with DBConn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS t_ui_layout_config (
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
                    form_column TEXT,
                    widget_type TEXT,
                    label_text TEXT,
                    tooltip TEXT,
                    
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
                )
            """)
            conn.commit()
            logging.info("UI layout configuration table created successfully")
            return True
    except Exception as e:
        logging.error(f"Error creating UI layout table: {e}")
        return False

def migrate_column_props_to_db(table_name, column_props_dict, config_version="1.0"):
    """
    Migrate existing COLUMN_PROPS dictionary to database
    
    Args:
        table_name: Name of the table
        column_props_dict: Dictionary of column properties (from ui_layout.py)
        config_version: Version identifier for this configuration
    """
    try:
        # Ensure table exists
        create_ui_layout_table()
        
        with DBConn() as conn:
            cursor = conn.cursor()
            current_time = datetime.now().isoformat()
            
            for column_name, props in column_props_dict.items():
                # Prepare data for insertion
                ui_config = {
                    'table_name': table_name,
                    'column_name': column_name,
                    'is_system_col': int(props.get('is_system_col', False)),
                    'is_user_key': int(props.get('is_user_key', False)),
                    'is_required': int(props.get('is_required', False)),
                    'is_visible': int(props.get('is_visible', True)),
                    'is_editable': int(props.get('is_editable', True)),
                    'is_clickable': int(props.get('is_clickable', False)),
                    'form_column': props.get('form_column', ''),
                    'widget_type': props.get('widget_type', 'text_input'),
                    'label_text': props.get('label_text', column_name.title()),
                    'tooltip': props.get('tooltip', ''),
                    'config_version': config_version,
                    'datatype': props.get('datatype', 'text'),
                    'created_at': current_time,
                    'updated_at': current_time,
                    'created_by': CURRENT_USER,
                    'updated_by': CURRENT_USER,
                    'is_active': 1
                }
                
                # Insert or replace configuration
                cursor.execute("""
                    INSERT OR REPLACE INTO t_ui_layout_config 
                    (table_name, column_name, is_system_col, is_user_key, is_required,
                     is_visible, is_editable, is_clickable, form_column, widget_type,
                     label_text, tooltip, config_version, datatype, created_at, 
                     updated_at, created_by, updated_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ui_config['table_name'], ui_config['column_name'],
                    ui_config['is_system_col'], ui_config['is_user_key'], ui_config['is_required'],
                    ui_config['is_visible'], ui_config['is_editable'], ui_config['is_clickable'],
                    ui_config['form_column'], ui_config['widget_type'], ui_config['label_text'],
                    ui_config['tooltip'], ui_config['config_version'], ui_config['datatype'],
                    ui_config['created_at'], ui_config['updated_at'], ui_config['created_by'],
                    ui_config['updated_by'], ui_config['is_active']
                ))
            
            conn.commit()
            logging.info(f"Migrated {len(column_props_dict)} column configurations for {table_name}")
            return True
            
    except Exception as e:
        logging.error(f"Error migrating column props to database: {e}")
        return False

def load_ui_config_from_db(table_name, config_version="1.0"):
    """
    Load UI configuration from database and return in COLUMN_PROPS format
    
    Args:
        table_name: Name of the table
        config_version: Version of configuration to load
        
    Returns:
        Dictionary in COLUMN_PROPS format
    """
    try:
        with DBConn() as conn:
            sql = """
                SELECT column_name, is_system_col, is_user_key, is_required,
                       is_visible, is_editable, is_clickable, form_column,
                       widget_type, label_text, tooltip, datatype
                FROM t_ui_layout_config 
                WHERE table_name = ? AND config_version = ? AND is_active = 1
                ORDER BY form_column, column_name
            """
            df = pd.read_sql(sql, conn, params=(table_name, config_version))
            
            if df.empty:
                logging.warning(f"No UI configuration found for {table_name} version {config_version}")
                return {}
            
            # Convert to COLUMN_PROPS format
            column_props = {}
            for _, row in df.iterrows():
                column_name = row['column_name']
                column_props[column_name] = {
                    'is_system_col': bool(row['is_system_col']),
                    'is_user_key': bool(row['is_user_key']),
                    'is_required': bool(row['is_required']),
                    'is_visible': bool(row['is_visible']),
                    'is_editable': bool(row['is_editable']),
                    'is_clickable': bool(row['is_clickable']),
                    'datatype': row['datatype'] or 'text',
                    'form_column': row['form_column'] or '',
                    'widget_type': row['widget_type'] or 'text_input',
                    'label_text': row['label_text'] or column_name.title(),
                    'tooltip': row['tooltip'] or ''
                }
            
            return column_props
            
    except Exception as e:
        logging.error(f"Error loading UI config from database: {e}")
        return {}

def save_ui_config_to_db(table_name, column_name, ui_properties, config_version="1.0"):
    """
    Save individual column UI configuration to database
    
    Args:
        table_name: Name of the table
        column_name: Name of the column
        ui_properties: Dictionary of UI properties
        config_version: Configuration version
    """
    try:
        # Ensure table exists
        create_ui_layout_table()
        
        with DBConn() as conn:
            current_time = datetime.now().isoformat()
            
            # Prepare data
            ui_config = {
                'table_name': table_name,
                'column_name': column_name,
                'is_system_col': int(ui_properties.get('is_system_col', False)),
                'is_user_key': int(ui_properties.get('is_user_key', False)),
                'is_required': int(ui_properties.get('is_required', False)),
                'is_visible': int(ui_properties.get('is_visible', True)),
                'is_editable': int(ui_properties.get('is_editable', True)),
                'is_clickable': int(ui_properties.get('is_clickable', False)),
                'form_column': ui_properties.get('form_column', ''),
                'widget_type': ui_properties.get('widget_type', 'text_input'),
                'label_text': ui_properties.get('label_text', column_name.title()),
                'tooltip': ui_properties.get('tooltip', ''),
                'config_version': config_version,
                'datatype': ui_properties.get('datatype', 'text'),
                'updated_at': current_time,
                'updated_by': CURRENT_USER
            }
            
            cursor = conn.cursor()
            
            # Check if configuration exists
            cursor.execute("""
                SELECT id FROM t_ui_layout_config 
                WHERE table_name = ? AND column_name = ? AND config_version = ?
            """, (table_name, column_name, config_version))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute("""
                    UPDATE t_ui_layout_config SET
                        is_system_col = ?, is_user_key = ?, is_required = ?,
                        is_visible = ?, is_editable = ?, is_clickable = ?,
                        form_column = ?, widget_type = ?, label_text = ?,
                        tooltip = ?, datatype = ?, updated_at = ?, updated_by = ?
                    WHERE table_name = ? AND column_name = ? AND config_version = ?
                """, (
                    ui_config['is_system_col'], ui_config['is_user_key'], ui_config['is_required'],
                    ui_config['is_visible'], ui_config['is_editable'], ui_config['is_clickable'],
                    ui_config['form_column'], ui_config['widget_type'], ui_config['label_text'],
                    ui_config['tooltip'], ui_config['datatype'], ui_config['updated_at'], 
                    ui_config['updated_by'], table_name, column_name, config_version
                ))
            else:
                # Insert new
                ui_config['created_at'] = current_time
                ui_config['created_by'] = CURRENT_USER
                ui_config['is_active'] = 1
                
                cursor.execute("""
                    INSERT INTO t_ui_layout_config 
                    (table_name, column_name, is_system_col, is_user_key, is_required,
                     is_visible, is_editable, is_clickable, form_column, widget_type,
                     label_text, tooltip, config_version, datatype, created_at, 
                     updated_at, created_by, updated_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ui_config['table_name'], ui_config['column_name'],
                    ui_config['is_system_col'], ui_config['is_user_key'], ui_config['is_required'],
                    ui_config['is_visible'], ui_config['is_editable'], ui_config['is_clickable'],
                    ui_config['form_column'], ui_config['widget_type'], ui_config['label_text'],
                    ui_config['tooltip'], ui_config['config_version'], ui_config['datatype'],
                    ui_config['created_at'], ui_config['updated_at'], ui_config['created_by'],
                    ui_config['updated_by'], ui_config['is_active']
                ))
            
            conn.commit()
            return True
            
    except Exception as e:
        logging.error(f"Error saving UI config to database: {e}")
        return False

def compile_ui_layout_from_db(output_file=None):
    """
    Generate ui_layout.py file from database configurations
    
    Args:
        output_file: Path to output file (default: ui_layout.py)
    """
    try:
        if output_file is None:
            output_file = os.path.join(os.path.dirname(__file__), 'ui_layout_generated.py')
        
        with DBConn() as conn:
            sql = """
                SELECT DISTINCT table_name FROM t_ui_layout_config 
                WHERE is_active = 1 
                ORDER BY table_name
            """
            tables_df = pd.read_sql(sql, conn)
            
            if tables_df.empty:
                logging.warning("No UI configurations found in database")
                return False
            
            # Generate Python code
            generated_code = [
                "# Generated UI Layout Configuration",
                "# Auto-generated from t_ui_layout_config table",
                f"# Generated at: {datetime.now().isoformat()}",
                "",
                "# Import statements",
                "from utils import BLANK_STR_VALUE",
                "",
                "COLUMN_PROPS = {"
            ]
            
            for _, table_row in tables_df.iterrows():
                table_name = table_row['table_name']
                column_props = load_ui_config_from_db(table_name)
                
                if column_props:
                    generated_code.append(f"    '{table_name}': {{")
                    
                    for column_name, props in column_props.items():
                        generated_code.append(f"        '{column_name}': {{")
                        for key, value in props.items():
                            if isinstance(value, str):
                                generated_code.append(f"            '{key}': '{value}',")
                            else:
                                generated_code.append(f"            '{key}': {value},")
                        generated_code.append("        },")
                    
                    generated_code.append("    },")
            
            generated_code.append("}")
            generated_code.append("")
            
            # Write to file
            with open(output_file, 'w') as f:
                f.write('\n'.join(generated_code))
            
            logging.info(f"Generated UI layout file: {output_file}")
            return True
            
    except Exception as e:
        logging.error(f"Error compiling UI layout from database: {e}")
        return False

def get_ui_config_versions(table_name):
    """Get all configuration versions for a table"""
    try:
        with DBConn() as conn:
            sql = """
                SELECT DISTINCT config_version, created_at, created_by
                FROM t_ui_layout_config 
                WHERE table_name = ? AND is_active = 1
                ORDER BY created_at DESC
            """
            df = pd.read_sql(sql, conn, params=(table_name,))
            return df.to_dict('records')
    except Exception as e:
        logging.error(f"Error getting UI config versions: {e}")
        return []

def dynamic_load_column_props(table_name, fallback_to_static=True):
    """
    Dynamically load COLUMN_PROPS for a table, with fallback to static configuration
    
    Args:
        table_name: Name of the table
        fallback_to_static: Whether to fallback to ui_layout.py if DB config not found
        
    Returns:
        Dictionary of column properties
    """
    try:
        # Try loading from database first
        db_config = load_ui_config_from_db(table_name)
        
        if db_config:
            logging.info(f"Loaded UI config from database for {table_name}")
            return db_config
        
        # Fallback to static configuration
        if fallback_to_static:
            try:
                from ui_layout import COLUMN_PROPS
                static_config = COLUMN_PROPS.get(table_name, {})
                if static_config:
                    logging.info(f"Using static UI config for {table_name}")
                    return static_config
            except ImportError:
                logging.warning("Could not import static ui_layout.py")
        
        logging.warning(f"No UI configuration found for {table_name}")
        return {}
        
    except Exception as e:
        logging.error(f"Error in dynamic column props loading: {e}")
        return {}

