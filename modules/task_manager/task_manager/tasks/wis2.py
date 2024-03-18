import base64
import datetime as dt
#from datetime import date, datetime, UTC
import importlib
import json
import logging
import os
from pathlib import Path
import pickle
import urllib3
from urllib.parse import urlsplit

from celery import Task

from celery.utils.log import get_task_logger

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError

from bufr2geojson import transform
from task_manager.db import session
from task_manager.worker import app as app

from station_metadata.utils import camel2snake
from wccdm.schema import *
from wccdm.utils import *

_pool = urllib3.PoolManager()
hash_module = importlib.import_module("hashlib")

# environment variables
DATA_BASEPATH = os.getenv("DATA",".")
MEASURE = "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement"
CATEGORICAL = "http//www.opengis.net/def/observationType/OGC-OM/2.0/OM_CategoryObservation"
UID = os.environ["POSTGRES_USER"]
PWD = os.environ["POSTGRES_PASSWORD"]
DBNAME = os.environ["POSTGRES_DB"]
DBHOST = os.environ["POSTGRES_HOST"]
DBPORT = os.environ["POSTGRES_PORT"]

#LOGGER = logging.getLogger(__name__)
#LOG_LEVEL = os.getenv("LOG_LEVEL","DEBUG").upper()
#LOGGER.setLevel(LOG_LEVEL)

LOGGER = get_task_logger(__name__)



class DBTask(Task):
    abstract = True
    def after_return(selfself, status, retval, task_id, args, kwargs, einfo):
        session.remove()

@app.task
def download_from_wis2(job):
    # get output directory
    LOGGER.debug(f"Processing job{json.dumps(job)}")
    target_directory = job.get("target",".")
    dataset = str(target_directory)

    # get date (used in output path due to number of files)
    today = dt.date.today()
    yyyy = f"{today.year:04}"
    mm = f"{today.month:02}"
    dd = f"{today.day:02}"
    target_directory = Path(DATA_BASEPATH)/target_directory/yyyy/mm/dd
    target_directory.mkdir(exist_ok=True, parents=True)

    # get identifiers
    data_id = job['payload']['properties']['data_id']
    metadata_id = job['payload']['properties'].get("metadata_id")
    message_id = job['payload']['id']
    # search links, find canonical and update
    canonical = None
    update = None
    canonical_length = None
    update_length = None
    for link in job['payload']['links']:
        if link['rel'] == 'canonical':
            canonical = link['href']
            canonical_length = link.get('length')
        if link['rel'] == 'update':
            update = link['href']
            update_length = link.get('length')

    # now check if we have hash
    hash_method = None
    hash_function = None
    hash_expected_value = None
    if 'integrity' in job['payload']['properties']:
        hash_method = job['payload']['properties']['integrity']['method']
        hash_expected_value = job['payload']['properties']['integrity']['value']  # noqa
        hash_function = getattr(hash_module, hash_method, None)

    # Get some diagnostic information to log
    broker = job['_broker']  # broker the message received from
    received = job['_received']  # time the message was received
    queued = job['_queued']  # time the message added to the queue

    # identify which download link to use
    download_url = None
    expected_length = None
    overwrite = False
    if update is not None:
        download_url = update
        expected_length = update_length
        overwrite = True
    elif canonical is not None:
        download_url = canonical
        expected_length =canonical_length

    # Now download (if we have link)
    if download_url is not None:
        path = urlsplit(link['href']).path
        cache = urlsplit(link['href']).hostname
        filename = os.path.basename(path)
        output_path = target_directory / filename
        status = ""
        valid_hash = None
        save = False
        filesize = None
        hash_base64 = None
        download_start = None
        download_end = None
        if (not output_path.is_file()) or overwrite:
            download_start = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%S")
            try:
                # download the data
                response = _pool.request('GET', download_url)
                # get file size
                filesize = len(response.data)
                # calculate hash of data if method supplied
                if None not in (hash_method, hash_function):
                    hash_value = hash_function(response.data).digest()
                    # convert to base64
                    hash_base64 = base64.b64encode(hash_value).decode()
            except Exception as e:
                status = "FAIL"
                pass
            # if we have hashes compare
            try:
                if None not in (hash_base64, hash_expected_value):
                    if hash_base64 == hash_expected_value:
                        save = True
                        valid_hash = True
                else:
                    save = True
                if save:
                    status = "SUCCESS"
                    output_path.write_bytes(response.data)
            except Exception as e:
                status = "FAIL"

            download_end = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%S")
        else:
            status = "SKIPPED"

        result = {
            'broker': broker,
            'message_id': message_id,
            'data_id': data_id,
            'metadata_id': metadata_id,
            'received': received,
            'queued': queued,
            'status': status,
            'cache': cache,
            'filename': str(target_directory / filename),
            'save': save,
            'valid_hash': valid_hash,
            'hash_method': hash_method,
            'expected_hash': hash_expected_value,
            'hash_value': hash_base64,
            'expected_length': expected_length,
            'filesize': filesize,
            'download_start': download_start,
            'download_end': download_end,
            'dataset': dataset
        }
    else:
        result = {}

    # print(json.dumps(result, indent=4))

    return result

@app.task(base=DBTask)
def decode_and_ingest(result):
    if result.get('status','FAILED') == 'SUCCESS':
        # DB connection
        #engine = create_engine(f"postgresql+psycopg2://{UID}:{PWD}@{DBHOST}:{DBPORT}/{DBNAME}")
        #with sessionmaker(bind=engine)() as session:
        # load BUFR data
        datafile = result.get('filename')
        with open(datafile, 'rb') as fh:
            bufr = fh.read()
        # convert / transform
        features = transform(bufr)
        observations = []
        is_member_of = result.get('dataset', 'NA')
        is_member_of = fetch_uri_id(Dataset, is_member_of, session)
        # iterate over features
        for obj in features:
            feature = obj.get("geojson")
            if feature is None:
                continue
            observation = {}
            if feature['geometry'] is None:
                LOGGER.error(f"Bad location in {datafile}, skipping")
                continue
            geom_type = feature['geometry']['type']
            if geom_type != "Point":
                raise NotImplementedError
            lon, lat = feature['geometry']['coordinates']
            if None in (lon, lat):
                LOGGER.error(f"Bad location in {datafile}, skipping")
                continue
            location = f"POINT({lon} {lat})"
            observation['location'] = location
            # extract properties, first value
            if feature['properties'].get('observationType') == MEASURE:
                observation['result_value'] = feature['properties'][
                    'result'].get('value')
                observation['result_units'] = feature['properties'][
                    'result'].get('units')
                observation['result_units'] = fetch_uri_id(Units, observation[
                    'result_units'], session)
                observation['result_uncertainty'] = feature['properties'][
                    'result'].get('standardUncertainty')
            elif feature['properties'].get('observationType') == CATEGORICAL:
                # check if we have flag or code table
                if 'flags' in feature['properties']['result']['value']:
                    observation['result_value'] = int(feature['properties']['result']['value']['entry'], 2)
                    observation['result_code_table'] = feature['properties']['result']['value']['flags']
                    observation['result_description'] = ""
                else:
                    observation['result_value'] = int(feature['properties']['result']['value']['entry'])
                    observation['result_code_table'] = feature['properties']['result']['value']['codetable']
                    observation['result_description'] = feature['properties']['result']['value']['description']
                observation['result_units'] = feature['properties']['result']['units']
                observation['result_uncertainty'] = feature['properties']['result']['standardUncertainty']
                observation['result_units'] = fetch_uri_id(Units, observation['result_units'],session)
                observation['result_code_table'] = fetch_uri_id(CodeTable,observation['result_code_table'],session)
            uri = feature['properties'].get('observationType')
            if uri is not None:
                observation['observation_type'] = fetch_uri_id(ObservationType,uri,session)
            uri = feature['properties'].get('observingProcedure')
            if uri is not None:
                observation['observing_procedure'] = fetch_uri_id(ObservingProcedure, uri,session)

            uri = feature['properties'].get('observedProperty')
            if uri is not None:
                observation['observed_property'] = fetch_uri_id(ObservedProperty, uri,session)

            uri = feature['properties'].get('host','UNKNOWN')
            if uri is not None:
                observation['host'] = fetch_uri_id(Host, uri,session)
            else:
                observation['host'] = fetch_uri_id(Host, "UNKNOWN", session)

            uri = feature['properties'].get('observer')
            if uri is not None:
                observation['observer'] = fetch_uri_id(Observer, uri,session)

            observation['is_member_of'] = is_member_of

            # parse date / time elements
            start, end, duration = time_parser(feature['properties']['phenomenonTime'])
            observation['phenomenon_time_start'] = start
            observation['phenomenon_duration'] = f"{duration.total_seconds()} seconds"
            observation['result_time'] = feature['properties']['resultTime']
            for k, v in feature['properties']['parameter'].items():
                if k not in ("additionalProperties", "reportType", "reportIdentifier","isMemberOf"):
                    key = camel2snake(k)
                    observation[key] = v

                                

            uri = feature['properties']['parameter']['reportType']
            if uri[0:3] == "006":
                LOGGER.error("Radar data, skipping")
                continue
            observation['report_type'] = fetch_uri_id(ReportType, uri,session)


            uri = feature['properties']['parameter']['reportIdentifier']
            observation['report_identifier'] = fetch_uri_id(ReportIdentifier,uri,session, use_cache=False)

            result_quality = list()
            for flag in feature['properties']['resultQuality']:
                if flag.get('inScheme') is not None:
                    result_quality.append(QualityFlag(
                        scheme=flag.get('inScheme'),
                        flag=flag.get('flag'),
                        value=flag.get('flagValue')))

            feature_of_interest = list()
            for foi in feature['properties']['featureOfInterest']:
                if foi.get('id') is not None:
                    feature_of_interest.append(Feature(
                        uri=foi.get('id'),
                        label=foi.get('label'),
                        relation=foi.get('relation')))

            observation['result_quality'] = result_quality
            observation['feature_of_interest'] = feature_of_interest
            try:
                observations.append(Observation(**observation))
            except Exception as e:
                LOGGER.eeror("Error appending observation, skipping")
                continue
        try:
            session.add_all(observations)
            session.commit()
            print(f"{len(observations)} observations added")
        except ProgrammingError as e:
            session.rollback()
            for o in observations:
                LOGGER.error("Adding 1")
                try:
                    session.add(o)
                    session.commit()
                except Exception as e:
                    LOGGER.error("Failed add 1")
                    LOGGER.error(e)
                    LOGGER.error(o)
                    session.rollback()
        except Exception as e:
            LOGGER.error(e)
            LOGGER.error("Error adding data, dumping to file")
            LOGGER.error(observations)
            session.rollback()

    else:
        pass


def clean_up():
    pass