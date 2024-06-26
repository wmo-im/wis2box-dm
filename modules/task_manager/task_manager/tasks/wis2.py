import base64
import datetime as dt
import importlib
import json
from multiprocessing import Process
import os
from pathlib import Path
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



observed_property_map = {
    "non_coordinate_pressure": {"id": 0, "preferred_label":"air_pressure", "uri": "http://codes.wmo.int/bufr4/b/10/004"},
    "pressure_reduced_to_mean_sea_level": {"id": 1, "preferred_label": "air_pressure_at_mean_sea_level", "uri": "http://codes.wmo.int/bufr4/b/10/051"},
    "air_temperature": {"id": 2, "preferred_label": "air_temperature", "uri": "http://codes.wmo.int/bufr4/b/12/101"},
    "dewpoint_temperature": {"id": 3, "preferred_label": "dew_point_temperature", "uri": "http://codes.wmo.int/bufr4/b/12/103"},
    "relative_humidity": {"id": 4, "preferred_label": "relative_humidity", "uri": "http://codes.wmo.int/bufr4/b/13/009"},
    "wind_direction": {"id": 5, "preferred_label": "wind_from_direction", "uri": "http://codes.wmo.int/bufr4/b/11/001"},
    "wind_speed": {"id": 6, "preferred_label": "wind_speed", "uri": "http://codes.wmo.int/bufr4/b/11/002"},
    "total_precipitation_or_total_water_equivalent": {"id": 7, "preferred_label": "precipitation_amount","uri": "http://codes.wmo.int/bufr4/b/13/011"},
    "total_snow_depth": {"id": 8, "preferred_label": "total_snow_depth", "uri": "http://codes.wmo.int/bufr4/b/13/013"},
    "depth_of_fresh_snow": {"id": 9, "preferred_label": "depth_of_fresh_snow", "uri": "http://codes.wmo.int/bufr4/b/13/012"}
}

report_type_map = {
  "000000": {
    "id": 1,
    "preferred_label": "Surface data - land: hourly synoptic observations from fixed-land stations (SYNOP)",
    "uri": "https://codes.wmo.int/common/13/0/0"
  },
  "000001": {
    "id": 2,
    "preferred_label": "Surface data - land: intermediate synoptic observations from fixed-land stations (SYNOP)",
    "uri": "https://codes.wmo.int/common/13/0/1"
  },
  "000002": {
    "id": 3,
    "preferred_label": "Surface data - land: main synoptic observations from fixed-land stations (SYNOP)",
    "uri": "https://codes.wmo.int/common/13/0/2"
  },
  "000006": {
    "id": 4,
    "preferred_label": "Surface data - land: one-hour observations from automated stations",
    "uri": "https://codes.wmo.int/common/13/0/6"
  },
  "000007": {
    "id": 5,
    "preferred_label": "Surface data - land: n-minute observations from AWS stations",
    "uri": "https://codes.wmo.int/common/13/0/7"
  },
  "001025": {
    "id": 6,
    "preferred_label": "Surface data - sea: buoy",
    "uri": "https://codes.wmo.int/common/13/1/25"
  }
}


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
                        valid_hash = False
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
            'broker': broker, # int -> varchar
            'message_id': message_id, # varchar
            'data_id': data_id, # varchar
            'metadata_id': metadata_id, # int -> varchar
            'received': received, # timestamp with timezone
            'queued': queued, # timestamp with timezone
            'status': status, # int -> varchar
            'cache': cache, # int -> varchar
            'filename': str(target_directory / filename), # varchar
            'save': save, # bool
            'valid_hash': valid_hash, # varchar
            'hash_method': hash_method, # int -> varchar
            'expected_hash': hash_expected_value, # varchar
            'hash_value': hash_base64, # varchar
            'expected_length': expected_length, # int
            'filesize': filesize, # int
            'download_start': download_start, # timestamp with time zone
            'download_end': download_end, # timestamp with time zone
            'dataset': dataset # int -> varchar
        }
    else:
        result = {}

    # print(json.dumps(result, indent=4))
    LOGGER.warning(json.dumps(result, indent=4))

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
            observation['observed_property'] = observed_property_map.get(uri, {}).get("id", None)
            if observation['observed_property'] is None:
                LOGGER.warning(f"Skipping observed property: {uri}")
                continue

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
            observation['phenomenon_time_end'] = end
            observation['phenomenon_duration'] = f"{duration.total_seconds()} seconds"
            observation['result_time'] = feature['properties']['resultTime']
            for k, v in feature['properties']['parameter'].items():
                if k not in ("additionalProperties", "reportType", "reportIdentifier","isMemberOf"):
                    key = camel2snake(k)
                    observation[key] = v


            uri = feature['properties']['parameter']['reportType']
            observation['report_type'] = report_type_map.get(uri, {}).get("id", 0)
            if observation['report_type'] is None:
                LOGGER.warning(f"Skipping report_type: {uri}")
                continue


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