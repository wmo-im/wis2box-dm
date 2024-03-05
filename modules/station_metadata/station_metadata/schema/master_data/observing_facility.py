import datetime

from geoalchemy2 import Geography
from sqlalchemy import (bindparam, create_engine, text, DateTime,
                        ForeignKey, ForeignKeyConstraint, Integer, MetaData,
                        String)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (mapped_column, relationship, DeclarativeBase,
                            Mapped, Session)

from station_metadata.schema import Base
from station_metadata.schema.reference_tables import *
from station_metadata.utils import *


class FacilityChildTable(Base):
    __abstract__ = True
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return camel2snake(cls.__name__)

    __table_args__ = {"schema": "wmdr"}
    id: Mapped[int] = mapped_column(primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("wmdr.observing_facility.id"))
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class ObservingFacility(Base):
    __tablename__ = "observing_facility"
    __table_args__ = {"schema":"wmdr"}
    id: Mapped[int] = mapped_column(primary_key=True)
    wsi: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    extension = mapped_column(JSONB, nullable=True)
    date_established: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_closed: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    wmo_region: Mapped[str] = mapped_column(ForeignKey("wmdr.wmo_region_code_list.notation"))
    facility_type: Mapped[str] = mapped_column(ForeignKey("wmdr.facility_type_code_list.notation"))
    # To do - add unique constraint on wsi


class FacilityDescription(FacilityChildTable):
    description: Mapped[str] = mapped_column(nullable = False)


class FacilityLocation(FacilityChildTable):
    location = mapped_column(Geography(geometry_type="POINTZ", srid=4326), nullable=True)
    geopositioning_method: Mapped[str] = mapped_column(ForeignKey("wmdr.geopositioning_method_code_list.notation"), nullable=True)


class FacilityOnlineResource(Base):
    __tablename__ = "facility_online_resource"
    __table_args__ = {"schema": "wmdr"}
    id: Mapped[int] = mapped_column(primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("wmdr.observing_facility.id"))
    uri: Mapped[str] = mapped_column(nullable=False)


class FacilityResponsibleParty(FacilityChildTable):
    individual_name: Mapped[str] = mapped_column(nullable=True)
    organisation_name: Mapped[str] = mapped_column(nullable=True)
    position_name: Mapped[str] = mapped_column(nullable=True)
    contact_info: Mapped[dict] = mapped_column(JSONB, nullable=True)
    role: Mapped[str] = mapped_column(nullable=True)
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class ProgramAffiliation(FacilityChildTable):
    program_affiliation: Mapped[str] = mapped_column(ForeignKey("wmdr.program_affiliation_code_list.notation"), nullable=False)
    reporting_status: Mapped[str] = mapped_column(ForeignKey("wmdr.reporting_status_code_list.notation"), nullable=False)
    program_specific_facility_id: Mapped[str] = mapped_column(nullable=True)


class ClimateZone(FacilityChildTable):
    climate_zone: Mapped[str] = mapped_column(ForeignKey("wmdr.climate_zone_code_list.notation"), nullable=False)


class SurfaceCover(FacilityChildTable):
    __table_args__ = (
        ForeignKeyConstraint(["surface_cover","scheme"],
                             ["wmdr.surface_cover_code_list.notation","wmdr.surface_cover_code_list.scheme"]),
        {"schema": "wmdr"})
    surface_cover: Mapped[str] = mapped_column(nullable=False)
    scheme: Mapped[str] = mapped_column(nullable=False)


class SurfaceRoughness(FacilityChildTable):
    pass


class Territory(FacilityChildTable):
    territory_name: Mapped[str] = mapped_column(ForeignKey("wmdr.territory_name_code_list.notation"), nullable=False)


class TopographyBathymetry(FacilityChildTable):
    altitude_or_depth: Mapped[str] = mapped_column(ForeignKey("wmdr.altitude_or_depth_code_list.notation"))
    local_topography: Mapped[str] = mapped_column(ForeignKey("wmdr.local_topography_code_list.notation"))
    relative_elevation: Mapped[str] = mapped_column(ForeignKey("wmdr.relative_elevation_code_list.notation"))
    topographic_context: Mapped[str] = mapped_column(ForeignKey("wmdr.topographic_context_code_list.notation"))
