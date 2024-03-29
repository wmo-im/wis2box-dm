from lxml import etree

from sqlalchemy import create_engine, text, ForeignKey, MetaData
from sqlalchemy.orm import sessionmaker

import urllib3

from station_metadata.schema.reference_tables import *
from station_metadata.schema.master_data.observing_facility import *
from station_metadata.utils.transforms import *

# set connection details
UID = os.environ["POSTGRES_USER"]
PWD = os.environ["POSTGRES_PASSWORD"]
DBNAME = os.environ["POSTGRES_DB"]
DBHOST = os.environ["POSTGRES_HOST"]
DBPORT = os.environ["POSTGRES_PORT"]


_http_pool = urllib3.PoolManager()


def import_station(wsi: str):

    engine = create_engine(f"postgresql+psycopg2://{UID}:{PWD}@{DBHOST}:{DBPORT}/{DBNAME}", echo=True)
    session = sessionmaker(bind=engine)()

    # first download data from OSCAR/Surface
    #_url = f"https://oscar.wmo.int/surface/rest/api/wmd/download/{wsi}"
    _url = f"https://oscar.wmo.int/oai/provider?verb=GetRecord&metadataPrefix=wmdr&identifier={wsi}"
    print(_url)
    resp = _http_pool.request("GET", _url)
    # check status
    if resp.status != 200:
        status = resp.status
        output = {
            "status": status,
            "msg": resp.msg
        }
        print("ERROR")
        return mimetype, output

    xml_text = resp.data.decode('utf-8')
    # fix new lines etc
    xml_text = re.sub(r'(?<!>)\n', ' ', xml_text)
    xml_text = re.sub(r'[ \t]+', ' ', xml_text)
    xml_text = re.sub(r'[ \t]<', '<', xml_text)
    xml_text = re.sub(r'"', "'", xml_text)

    # now read as xml
    xml = etree.fromstring(xml_text.encode('utf-8'))
    nsmap = {'oai': 'http://www.openarchives.org/OAI/2.0/'}

    records = xml.xpath('//oai:metadata/*', namespaces=nsmap)
    for record in records:


        data = extract_observing_facility(record)
        host = ObservingFacility(**data)
        session.add_all([host])
        session.flush()

        # now add other attributes
        data = extract_facility_location(record, host.id)
        locations = list()
        for location in data:
            locations.append(FacilityLocation(**location))

        data = extract_program_affiliation(record, host.id)
        affiliations = list()
        for affiliation in data:
            if affiliation['program_affiliation'] is None:
                continue
            affiliations.append(ProgramAffiliation(**affiliation))

        data = extract_facility_description(record, host.id)
        host_descriptions = list()
        for description in data:
            host_descriptions.append(FacilityDescription(**description))

        data = extract_facility_online_resource(record, host.id)
        facility_online_resources = list()
        for resource in data:
            facility_online_resources.append(FacilityOnlineResource(**resource))

        data = extract_facility_responsible_party(record, host.id)
        facility_responsible_parties = list()
        for party in data:
            facility_responsible_parties.append(FacilityResponsibleParty(**party))

        data = extract_surface_cover(record,host.id)
        surface_covers = list()
        for cover in data:
            surface_covers.append(SurfaceCover(**cover))

        data = extract_territory(record,host.id)
        territories = list()
        for territory in data:
            territories.append(Territory(**territory))

        data = extract_topography_bathymetry(record,host.id)
        topography_bathymetries = list()
        for topography in data:
            topography_bathymetries.append(TopographyBathymetry(**topography))

        session.add_all( locations + affiliations + host_descriptions +
                         facility_online_resources + facility_responsible_parties +
                         surface_covers + territories + topography_bathymetries)
    session.commit()
    session.close()
