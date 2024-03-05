from sqlalchemy import bindparam, text, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (mapped_column, relationship, DeclarativeBase,
                            Mapped, Session)

from station_metadata.schema import Base
from station_metadata.utils import camel2snake

class CodeList(Base):
    __abstract__ = True
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return camel2snake(cls.__name__)

    __table_args__ = {"schema": "wmdr"}
    notation: Mapped[str] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    uri: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=True)


class ClimateZoneCodeList(CodeList):
    pass


class RepresentativenessCodeList(CodeList):
    pass


class SurfaceCoverClassificationCodeList(CodeList):
    pass


class SurfaceCoverCodeList(CodeList):
    scheme: Mapped[str] = mapped_column(ForeignKey("wmdr.surface_cover_classification_code_list.notation"), primary_key=True)


class AltitudeOrDepthCodeList(CodeList):
    pass


class SurfaceRoughnessCodeList(CodeList):
    scheme: Mapped[str] = mapped_column(String, primary_key = True)


class ObservingMethodCodeList(CodeList):
    domain: Mapped[str] = mapped_column(String, primary_key = True)


class ApplicationAreaCodeList(CodeList):
    pass


class ControlLocationCodeList(CodeList):
    pass


class ControlStandardTypeCodeList(CodeList):
    pass


class CoordinateReferenceSystemCodeList(CodeList):
    pass


class DataCommunicationMethodCodeList(CodeList):
    pass


class DataFormatCodeList(CodeList):
    pass


class DataPolicyCodeList(CodeList):
    pass


class DomainCodeList(CodeList):
    pass


class EventAtFacilityCodeList(CodeList):
    pass


class ExposureCodeList(CodeList):
    pass


class FacilityTypeCodeList(CodeList):
    pass


class FrequencyUseCodeList(CodeList):
    pass


class GeometryCodeList(CodeList):
    pass


class GeopositioningMethodCodeList(CodeList):
    pass


class InstrumentControlResultCodeList(CodeList):
    pass


class InstrumentOperatingStatusCodeList(CodeList):
    pass


class LevelOfDataCodeList(CodeList):
    pass


class LocalTopographyCodeList(CodeList):
    pass


class MatrixCodeList(CodeList):
    pass


class ObservationStatusCodeList(CodeList):
    pass


class ObservedLayerCodeList(CodeList):
    pass


class ParticleSizeRangeCodeList(CodeList):
    pass


class PolarizationCodeList(CodeList):
    pass


class ProgramAffiliationCodeList(CodeList):
    pass


class PurposeOfFrequencyUseCodeList(CodeList):
    pass


class QualityFlagSystemCodeList(CodeList):
    pass


class ReferenceSurfaceTypeCodeList(CodeList):
    pass


class ReferenceTimeCodeList(CodeList):
    pass


class RelativeElevationCodeList(CodeList):
    pass


class ReportingStatusCodeList(CodeList):
    pass


class SampleTreatmentCodeList(CodeList):
    pass


class SamplingStrategyCodeList(CodeList):
    pass


class SourceOfObservationCodeList(CodeList):
    pass


class StationPictureDirectionCodeList(CodeList):
    pass


class TerritoryNameCodeList(CodeList):
    pass


class TimeStampMeaningCodeList(CodeList):
    pass


class TimezoneCodeList(CodeList):
    pass


class TopographicContextCodeList(CodeList):
    pass


class TraceabilityCodeList(CodeList):
    pass


class TransmissionModeCodeList(CodeList):
    pass


class UncertaintyEstimateProcedureCodeList(CodeList):
    pass


class WIGOSFunctionCodeList(CodeList):
    pass


class WMORegionCodeList(CodeList):
    pass


class WaterML2_0CodeList(CodeList):
    pass


class UnitCodeList(CodeList):
    pass


class ObservedVariableCodeList(CodeList):
    domain: Mapped[str] = mapped_column(String, primary_key = True)
