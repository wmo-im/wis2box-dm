import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from lxml import etree

THISDIR = os.path.dirname(os.path.realpath(__file__))
TRANSFORMS = Path(THISDIR) / "xslt"

def uri_leaf(uri):
    if uri in ("", None):
        return None
    leaf = urlparse(uri).path
    leaf = os.path.basename(leaf)
    return leaf

def fix_timestamp(timestamp):
    if timestamp not in (None, ""):
        timestamp = re.sub(r'[TZ]',r' ',timestamp)
    else:
        timestamp = None
    return timestamp


def extract_observing_facility(input_xml):
    # XSL transform
    with open(TRANSFORMS / "observing_facility.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    # convert to dict
    data = json.loads(record)
    # remove T and Z from date elements
    data["date_established"] = fix_timestamp(data["date_established"])
    data["date_closed"] = fix_timestamp(data["date_closed"])
    # parse uri for wmo region and station type, extracting notation
    data["wmo_region"] =  uri_leaf(data['wmo_region'])
    if data["wmo_region"] is None:
        data["wmo_region"] = "unknown"
    data["facility_type"] =  uri_leaf(data['facility_type'])
    return data

def extract_facility_description(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "facility_description.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        del data['wsi']
        yield data

def extract_facility_location(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "facility_location.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        # convert to dict
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        data["location"] = f"POINT({data['longitude']} {data['latitude']} {data['elevation']})"
        data["geopositioning_method"] = uri_leaf(data["geopositioning_method"])
        del data['longitude']
        del data['latitude']
        del data['elevation']
        del data['wsi']
        yield data

def extract_facility_online_resource(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "facility_online_resource.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        # convert to dict
        data = json.loads(line)
        data["facility_id"] = facility_id
        del data['wsi']
        yield data

def extract_facility_responsible_party(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "facility_responsible_party.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        # convert to dict
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        del data['wsi']
        yield data

def extract_program_affiliation(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "facility_program_affiliation.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        data["program_affiliation"] = uri_leaf(data["program_affiliation"])
        data["reporting_status"] = uri_leaf(data["reporting_status"])
        data["program_specific_facility_id"] = None if data["program_specific_facility_id"] == "" else data["program_specific_facility_id"]
        del data["wsi"]
        yield data

def extract_climate_zone(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "climate_zone.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        data["climate_zone"] = uri_leaf(data["climate_zone"])
        del data['wsi']
        yield data

def extract_surface_cover(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "surface_cover.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        data["surface_cover"] = uri_leaf(data["surface_cover"])
        data["scheme"] = uri_leaf(data["scheme"])
        del data['wsi']
        yield data

def extract_surface_roughness(input_xml, facility_id = None):
    raise NotImplementedError

def extract_territory(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "territory.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        data["territory_name"] = uri_leaf(data["territory_name"])
        del data['wsi']
        yield data

def extract_topography_bathymetry(input_xml, facility_id = None):
    # XSL transform
    with open(TRANSFORMS / "topography_bathymetry.xslt") as fh:
        xslt = fh.read()
    xslt_root = etree.fromstring(bytes(xslt, encoding="utf8"))
    # run transform
    transform = etree.XSLT(xslt_root)
    # extract record
    record = str(transform(input_xml))
    for line in record.splitlines():
        if len(line) == 0:
            continue
        data = json.loads(line)
        # fix fields
        data["facility_id"] = facility_id
        data["valid_from"] = fix_timestamp(data["valid_from"])
        data["valid_to"] = fix_timestamp(data["valid_to"])
        data["altitude_or_depth"] = uri_leaf(data["altitude_or_depth"])
        data["local_topography"] = uri_leaf(data["local_topography"])
        data["relative_elevation"] = uri_leaf(data["relative_elevation"])
        data["topographic_context"] = uri_leaf(data["topographic_context"])
        del data['wsi']
        yield data