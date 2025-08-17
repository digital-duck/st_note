from utils import *


# from dotenv import load_dotenv  # type: ignore
# load_dotenv()

st.set_page_config(
    page_title="Note📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data(ttl=3600)
def create_tables(file_ddl: str = CFG["META_DB_DDL"]):
    # run a test query
    ddl_script = open(file_ddl).read()
    # logging.error(ddl_script)
    with DBConn() as _conn:
        db_run_sql(ddl_script, _conn)
            
if __name__ == '__main__':
    # create tables if missing
    create_tables()

