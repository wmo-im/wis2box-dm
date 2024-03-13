import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

UID = os.environ["POSTGRES_USER"]
PWD = os.environ["POSTGRES_PASSWORD"]
DBNAME = os.environ["POSTGRES_DB"]
DBHOST = os.environ["POSTGRES_HOST"]
DBPORT = os.environ["POSTGRES_PORT"]

engine = create_engine(f"postgresql+psycopg2://{UID}:{PWD}@{DBHOST}:{DBPORT}/{DBNAME}")
session = scoped_session(sessionmaker(autocommit = False, autoflush = False, bind = engine))