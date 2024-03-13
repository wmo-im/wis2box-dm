import os
import re
from io import StringIO
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# set connection details
UID = os.environ["POSTGRES_USER"]
PWD = os.environ["POSTGRES_PASSWORD"]
DBNAME = os.environ["POSTGRES_DB"]
DBHOST = os.environ["POSTGRES_HOST"]
DBPORT = os.environ["POSTGRES_PORT"]

engine = create_engine(f"postgresql+psycopg2://{UID}:{PWD}@{DBHOST}:{DBPORT}/{DBNAME}", echo=True)

session = sessionmaker(bind=engine)()
cursor = session.connection().connection.cursor()

code_tables = ["AltitudeOrDepth", "ApplicationArea", "ClimateZone",
               "ControlLocation", "ControlStandardType",
               "CoordinateReferenceSystem", "DataCommunicationMethod",
               "DataFormat", "DataPolicy", "Domain", "EventAtFacility",
               "Exposure", "FacilityType", "FrequencyUse", "Geometry",
               "GeopositioningMethod", "InstrumentControlResult",
               "InstrumentOperatingStatus", "LevelOfData", "LocalTopography",
               "Matrix", "ObservationStatus", "ObservedLayer",
               "ParticleSizeRange", "Polarization", "ProgramAffiliation",
               "PurposeOfFrequencyUse", "QualityFlagSystem",
               "ReferenceSurfaceType", "ReferenceTime", "RelativeElevation",
               "ReportingStatus", "Representativeness",
               "SampleTreatment", "SamplingStrategy", "SourceOfObservation",
               "StationPictureDirection", "TerritoryName", "TimeStampMeaning",
               "Timezone", "TopographicContext", "Traceability",
               "TransmissionMode",
               "UncertaintyEstimateProcedure", "WIGOSFunction", "WMORegion",
               "WaterML2_0",
               "SurfaceCoverClassification"
               ]


column_map = {
    "@id": "uri",
    #"@notation": "notation",
    "dct:description": "description",
    "rdf:type": "type",
    "rdfs:label": "label",
    "@status": "status",
    "skos:notation": "notation"
}

def camel2snake(camel: str) -> str:
    # insert _ between lower and upper case characters
    snake = re.sub(r'([a-z])([A-Z])',r'\1_\2',camel)
    # insert _ between upper case and number
    snake = re.sub(r'([A-Z])([0-9])', r'\1_\2', snake)
    # insert _ between number and letter
    snake = re.sub(r'([0-9])([a-zA-Z])', r'\1_\2', snake)
    # finally 2+ upper followed by 1 upper, 1 lower
    snake = re.sub(r'([A-Z]{2,})([A-Z][a-z])', r'\1_\2', snake)
    return snake.lower()


for table in code_tables:
    print(f"Processing {table}")
    _url = f"https://codes.wmo.int/wmdr/{table}?_format=csv&_view=with_metadata"
    table = camel2snake(table)
    entries = pd.read_csv(_url)
    entries.rename(columns=column_map, inplace=True)
    # remove <> from uri's
    entries['uri']= entries['uri'].str.replace(r"\<|\>", "", regex=True)
    # remove ''@en from description
    entries['description'] = entries['description'].str.replace(r"'|@en", "",regex=True)
    # create input to DB, use buffer
    buffer = StringIO()
    entries[ ['notation','label','description','uri','type','status'] ].to_csv(buffer, sep="|", quoting=None, index=False)
    buffer.seek(0)
    cursor.copy_expert(f"COPY wmdr.{table}_code_list FROM STDIN WITH CSV HEADER DELIMITER AS '|'",buffer)

for table in ['unit']:
    print(f"Processing {table}")
    _url = f"https://codes.wmo.int/wmdr/{table}?_format=csv"
    table = camel2snake(table)
    entries = pd.read_csv(_url)
    entries.rename(columns=column_map, inplace=True)
    # remove <> from uri's
    entries['uri']= entries['uri'].str.replace(r"\<|\>", "", regex=True)
    # remove ''@en from description
    entries['description'] = entries['description'].str.replace(r"'|@en", "",regex=True)
    entries['status'] = None
    # create input to DB, use buffer
    buffer = StringIO()
    entries[ ['notation','label','description','uri','type','status'] ].to_csv(buffer, sep="|", quoting=None, index=False)
    buffer.seek(0)
    cursor.copy_expert(f"COPY wmdr.{table}_code_list FROM STDIN WITH CSV HEADER DELIMITER AS '|'",buffer)

domains = ["Atmosphere", "Earth", "Ocean", "OuterSpace", "Terrestrial"]
for domain in domains:
    table = "ObservedVariable"
    _url = f"https://codes.wmo.int/wmdr/{table}{domain}?_format=csv&_view=with_metadata"
    table = camel2snake(table)
    entries = pd.read_csv(_url)
    entries.rename(columns=column_map, inplace=True)
    entries = entries.assign(domain=domain)
    # remove <> from uri's
    entries['uri']= entries['uri'].str.replace(r"\<|\>", "", regex=True)
    # remove ''@en from description
    entries['description'] = entries['description'].str.replace(r"'|@en", "",regex=True)
    buffer = StringIO()
    entries[ ['domain','notation','label','description','uri','type','status'] ].to_csv(buffer, sep="|", quoting=None, index=False)
    buffer.seek(0)
    cursor.copy_expert(f"COPY wmdr.{table}_code_list FROM STDIN WITH CSV HEADER DELIMITER AS '|'",buffer)


domains = ["Atmosphere", "Ocean", "Terrestrial"]
for domain in domains:
    table = "ObservingMethod"
    print(f"{table}{domain}")
    _url = f"https://codes.wmo.int/wmdr/{table}{domain}?_format=csv&_view=with_metadata"
    table = camel2snake(table)
    entries = pd.read_csv(_url)
    entries.rename(columns=column_map, inplace=True)
    entries = entries.assign(domain=domain)
    # remove <> from uri's
    entries['uri']= entries['uri'].str.replace(r"\<|\>", "", regex=True)
    # remove ''@en from description
    entries['description'] = entries['description'].str.replace(r"'|@en", "",regex=True)
    buffer = StringIO()
    entries[ ['notation','domain','label','description','uri','type','status'] ].to_csv(buffer, sep="|", quoting=None, index=False)
    buffer.seek(0)
    cursor.copy_expert(f"COPY wmdr.{table}_code_list FROM STDIN WITH CSV HEADER DELIMITER AS '|'",buffer)

schemes = {"Glob2009":"globCover2009","IGBP":"igbp","LAI":"laifpar",
           "LCCS":"lccs","NPP":"npp","PFT":"pft","UMD":"umd"}
for key,scheme in schemes.items():
    table = "SurfaceCover"
    print(f"{table}{key}")
    _url = f"https://codes.wmo.int/wmdr/{table}{key}?_format=csv&_view=with_metadata"
    table = camel2snake(table)
    entries = pd.read_csv(_url)
    entries.rename(columns=column_map, inplace=True)
    entries = entries.assign(scheme=scheme)
    # remove <> from uri's
    entries['uri']= entries['uri'].str.replace(r"\<|\>", "", regex=True)
    # remove ''@en from description
    entries['description'] = entries['description'].str.replace(r"'|@en", "",regex=True)
    buffer = StringIO()
    entries[ ['scheme','notation','label','description','uri','type','status'] ].to_csv(buffer, sep="|", quoting=None, index=False)
    buffer.seek(0)
    cursor.copy_expert(f"COPY wmdr.{table}_code_list FROM STDIN WITH CSV HEADER DELIMITER AS '|'",buffer)

schemes = {"Davenport":"Davenport"}
for key,scheme in schemes.items():
    table = "SurfaceRoughness"
    print(f"{table}{key}")
    _url = f"https://codes.wmo.int/wmdr/{table}{key}?_format=csv&_view=with_metadata"
    table = camel2snake(table)
    entries = pd.read_csv(_url)
    entries.rename(columns=column_map, inplace=True)
    entries = entries.assign(scheme=scheme)
    # remove <> from uri's
    entries['uri']= entries['uri'].str.replace(r"\<|\>", "", regex=True)
    # remove ''@en from description
    entries['description'] = entries['description'].str.replace(r"'|@en", "",regex=True)
    buffer = StringIO()
    entries[ ['notation','scheme','label','description','uri','type','status'] ].to_csv(buffer, sep="|", quoting=None, index=False)
    buffer.seek(0)
    cursor.copy_expert(f"COPY wmdr.{table}_code_list FROM STDIN WITH CSV HEADER DELIMITER AS '|'",buffer)


session.commit()
session.close()

# The following is missing from the code list
# insert into wmdr.program_affiliation_code_list values ('ANTON','ANTON','Antarctic Observing Network','http://codes.wmo.int/wmdr/ProgramAffiliation/ANTON','skos:Concept','deprecated');