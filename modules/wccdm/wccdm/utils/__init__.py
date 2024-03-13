from dateutil import parser
from psycopg2.errors import UniqueViolation
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError
import time


from wccdm.schema import *

from celery.utils.log import get_task_logger

from threading import Lock

#LOGGER = logging.getLogger(__name__)
#LOG_LEVEL = os.getenv("LOG_LEVEL","DEBUG").upper()
#LOGGER.setLevel(LOG_LEVEL)

LOGGER = get_task_logger(__name__)

_URIs = {}
def fetch_uri_id(table_class, uri, session, use_cache = True):
    table = table_class.__table__
    schema = table.schema
    tablename = table.name

    if use_cache:  # first check if uri id cached
        if table not in _URIs:
            _URIs[table] = {}
            uri_id = None
        else:
            uri_id = _URIs[table].get(uri)
        if uri_id is not None:
            return uri_id

    # ID not cached, first check DB
    query = select(table_class).where(table_class.uri == uri)
    result = session.execute(query).fetchall()
    if not isinstance(result, list):
        result = [result]
    assert len(result) <= 1

    # we have result, return (and cache is specified)
    if len(result) == 1:
        if use_cache:
            _URIs[table][uri] = (result[0][0]).id
        return (result[0][0]).id


    # if we have reached here we need to insert new item
    # First try and acquire lock on DB table
    max_retries = 10
    retries = 0
    while retries < max_retries:
        try:
            # get lock on table
            session.begin_nested()
            session.execute(text(
                f"LOCK TABLE {schema}.{tablename} IN SHARE ROW EXCLUSIVE MODE"))
            session.commit()
        except OperationalError as e:
            session.rollback()
            time.sleep(0.01*retries)
            retries += 1
            if retries == max_retries:
                raise e  # Reraise the exception if max retries reached
            else:
                continue  # Retry acquiring the lock
        else:
            break  # Lock acquired successfully, exit the loop
    # check to make sure entry hasn't been created whilst waiting for lock
    query = select(table_class).where(table_class.uri == uri)
    result = session.execute(query).fetchall()
    if not isinstance(result, list):
        result = [result]
    assert len(result) <= 1
    # we have result, return (and cache is specified)
    if len(result) == 1:
        if use_cache:
            _URIs[table][uri] = (result[0][0]).id
        return (result[0][0]).id

    # now add to table
    try:
        new_uri = table_class(uri=uri)
        session.add_all([new_uri])
        session.commit()
    except IntegrityError as e:
        session.rollback()

        # try one last fetch, error suggests already in DB.
        query = select(table_class).where(table_class.uri == uri)
        result = session.execute(query).fetchall()
        if not isinstance(result, list):
            result = [result]
        # we have result, return (and cache is specified)
        if len(result) == 1:
            if use_cache:
                _URIs[table][uri] = (result[0][0]).id
            return (result[0][0]).id
        else:
            LOGGER.error(e)
            raise e

    if use_cache:
        _URIs[table][uri] = new_uri.id
    return new_uri.id


def time_parser(timestamp):
    if timestamp is None:
        return None, None, None
    if "/" in timestamp:
        start, end = timestamp.split("/")
        end = parser.isoparse(end)
        start = parser.isoparse(start)
    else:
        end = parser.isoparse(timestamp)
        start = end
    duration = end - start

    return start, end, duration