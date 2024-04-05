import os

from sqlalchemy import create_engine, text

# set connection details
UID = os.environ["POSTGRES_USER"]
PWD = os.environ["POSTGRES_PASSWORD"]
DBNAME = os.environ["POSTGRES_DB"]
DBHOST = os.environ["POSTGRES_HOST"]
DBPORT = os.environ["POSTGRES_PORT"]

# Import tables to create
from collection_manager.schema import *

engine = create_engine(f"postgresql+psycopg2://{UID}:{PWD}@{DBHOST}:{DBPORT}/{DBNAME}", echo=True)

with engine.begin() as conn:
    conn.execute(text("DROP SCHEMA IF EXISTS pygeoapi CASCADE"))
    # Create schema
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS pygeoapi"))
    # Add PostGIS extension
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS Postgis;"))

Base.metadata.create_all(engine)