import datetime as dt
import json
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import tables to create
from wccdm.schema import *

# set connection details
UID = os.environ["POSTGRES_USER"]
PWD = os.environ["POSTGRES_PASSWORD"]
DBNAME = os.environ["POSTGRES_DB"]
DBHOST = os.environ["POSTGRES_HOST"]
DBPORT = os.environ["POSTGRES_PORT"]

THISDIR = os.path.dirname(os.path.realpath(__file__))

engine = create_engine(f"postgresql+psycopg2://{UID}:{PWD}@{DBHOST}:{DBPORT}/{DBNAME}", echo=True)

# Creating a sessionmaker object bound to our engine
Session = sessionmaker(bind=engine)

# Creating a session object
session = Session()

with engine.begin() as conn:
    conn.execute(text("DROP SCHEMA IF EXISTS wccdm CASCADE"))
    # Create schema
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS wccdm"))
    # Add PostGIS extension
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS Postgis;"))

Base.metadata.create_all(engine)

# Add code table entries (where known)
infile = Path(THISDIR).parent / "tables" / "observed_property.json"
with open(infile) as fh:
    entries = json.load(fh)

to_add = []
for key, value in entries.items():
    to_add.append(ObservedProperty(**value))

session.add_all(to_add)
session.commit()


# Add code table entries (where known)
infile = Path(THISDIR).parent / "tables" / "report_type.json"
with open(infile) as fh:
    entries = json.load(fh)

to_add = []
for key, value in entries.items():
    to_add.append(ReportType(**value))

session.add_all(to_add)
session.commit()


# create list of days / dates to partition into
start_date = dt.datetime(2024, 1, 1)
end_date = dt.datetime(2024 ,12, 31)
date_list = []
current_date = start_date
while current_date <= end_date:
    date_list.append(current_date)
    current_date += dt.timedelta(days=1)

# create child tables
for day in date_list:

    start_date = day
    end_date = start_date + dt.timedelta(days=1)

    sql_statement = """
         CREATE TABLE wccdm.observation_{date}(
             CHECK (
                 phenomenon_time_end >= timestamp with time zone {s}
                 and phenomenon_time_end < timestamp with time zone {e}
                 )
         ) INHERITS (wccdm.observation)    
    """.format(date=day.strftime("%Y%m%d"),
               s = start_date.strftime("%Y-%m-%d 00:00+0"),
               e = end_date.strftime("%Y-%m-%d 00:00+0"))

    # Execute the SQL statement using the session and pass parameters
    session.execute(text(sql_statement))
    # Commit the changes
    session.commit()

# now triggers
sql_statement = ""
_if = "IF"
for day in date_list:
    start_date = day
    end_date = start_date + dt.timedelta(days=1)
    sql_statement += """
        {eif} (
            NEW.phenomenon_time_end >= timestamp with time zone '{s}'
            AND NEW.phenomenon_time_end < timestamp with time zone '{e}'
        ) THEN
        INSERT INTO wccdm.observation_{date} VALUES (NEW.*);    
    """.format(
        eif = _if,
        s = start_date.strftime("%Y-%m-%d 00:00+0"),
        e = end_date.strftime("%Y-%m-%d 00:00+0"),
        date = day.strftime("%Y%m%d"))
    _if = "ELSIF"

sql_statement = """
        CREATE OR REPLACE FUNCTION wccdm.observation_insert_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
    """ + sql_statement

sql_statement += """
        ELSE
            RAISE EXCEPTION 'Date out of range';
        END IF;
        RETURN NULL;
        END;
        $$
        LANGUAGE plpgsql;
    """

session.execute(text(sql_statement))
session.commit()

sql_statement = """
        CREATE TRIGGER insert_observation
        BEFORE INSERT ON wccdm.observation
        FOR EACH ROW EXECUTE PROCEDURE wccdm.observation_insert_trigger();
"""
session.execute(text(sql_statement))
session.commit()

session.close()

