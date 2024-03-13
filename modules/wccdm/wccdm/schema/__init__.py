import datetime
from typing import List, Union

from geoalchemy2 import Geography
from sqlalchemy import (bindparam, create_engine, text, DateTime,
                        ForeignKey, ForeignKeyConstraint, Integer, MetaData,
                        String, BigInteger, Numeric)
from sqlalchemy.dialects.postgresql import JSONB, INTERVAL
from sqlalchemy.orm import (mapped_column, relationship, registry,
                            DeclarativeBase, Mapped, Session)


mapper_registry = registry()
Base = mapper_registry.generate_base()

numeric = Union[int, float]

class Observation(Base):
    __tablename__ = "observation"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    location = mapped_column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    z_coordinate: Mapped[dict] = mapped_column(JSONB, nullable=True)
    host: Mapped[int] = mapped_column(ForeignKey("wccdm.host.id"), nullable=False)
    observer: Mapped[int] = mapped_column(ForeignKey("wccdm.observer.id"), nullable=True)
    #observation_type: Mapped[str] = mapped_column(String, nullable=True)
    observation_type: Mapped[int] = mapped_column(ForeignKey("wccdm.observation_type.id"), nullable=False)
    observed_property: Mapped[int] = mapped_column(ForeignKey("wccdm.observed_property.id"), nullable=False)
    observing_procedure: Mapped[int] = mapped_column(ForeignKey("wccdm.observing_procedure.id"), nullable=False)
    phenomenon_time_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    phenomenon_duration: Mapped[str] = mapped_column(INTERVAL, default = "0 seconds", nullable=True)
    result_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_time_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_time_duration: Mapped[str] = mapped_column(INTERVAL, nullable = True)
    has_provenance: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String, nullable=True)
    comment: Mapped[str] = mapped_column(String, nullable=True)
    report_type: Mapped[int] = mapped_column(ForeignKey("wccdm.report_type.id"), nullable=False)
    report_identifier: Mapped[int] = mapped_column(ForeignKey("wccdm.report_identifier.id"), nullable=False)
    is_member_of: Mapped[int] = mapped_column(ForeignKey("wccdm.dataset.id"), nullable=False)
    additional_properties: Mapped[str] = mapped_column(JSONB, nullable=True)
    # result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result_value: Mapped[numeric] = mapped_column(Numeric, nullable=True)
    result_units: Mapped[int] = mapped_column(ForeignKey("wccdm.units.id"), nullable=True)
    result_uncertainty: Mapped[numeric] = mapped_column(Numeric, nullable=True)
    result_code_table: Mapped[int] = mapped_column(ForeignKey("wccdm.code_table.id"), nullable=True)
    result_description: Mapped[str] = mapped_column(String, nullable=True)
    feature_of_interest: Mapped[List["Feature"]] = relationship(
        back_populates="observation", cascade="all, delete-orphan"
    )
    result_quality: Mapped[List["QualityFlag"]] = relationship(
        back_populates="observation", cascade="all, delete-orphan"
    )


class QualityFlag(Base):
    __tablename__ = "quality_flag"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    observation_id: Mapped[int] = mapped_column(ForeignKey("wccdm.observation.id"), nullable=False)
    observation: Mapped["Observation"] = relationship(back_populates="result_quality")
    scheme: Mapped[str] = mapped_column(String, nullable=False)
    flag: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    extension: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Feature(Base):
    __tablename__ = "feature"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    observation_id: Mapped[int] = mapped_column(ForeignKey("wccdm.observation.id"), nullable=False)
    observation: Mapped["Observation"] = relationship(back_populates="feature_of_interest")
    uri: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    relation: Mapped[str] = mapped_column(String, nullable=False)
    extension: Mapped[dict] = mapped_column(JSONB, nullable=True)

class URIStore(Base):
    __tablename__ = "uri_store"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uri: Mapped[str] = mapped_column(String, nullable=False, unique=True)

class ReportIdentifier(Base):
    __tablename__ = "report_identifier"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri: Mapped[str] = mapped_column(String, nullable=False, unique=True)

class ReportType(Base):
    __tablename__ = "report_type"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri: Mapped[str] = mapped_column(String, nullable=False, unique=True)

class Host(Base):
    __tablename__ = "host"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)


class ObservationType(Base):
    __tablename__ = "observation_type"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)


class ObservingProcedure(Base):
    __tablename__ = "observing_procedure"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)


class ObservedProperty(Base):
    __tablename__ = "observed_property"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)

class Observer(Base):
    __tablename__ = "observer"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)

class Units(Base):
    __tablename__ = "units"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)

class CodeTable(Base):
    __tablename__ = "code_table"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)

class Dataset(Base):
    __tablename__ = "dataset"
    __table_args__ = {"schema": "wccdm"}
    id: Mapped["int"] = mapped_column(BigInteger, primary_key=True)
    uri:  Mapped[str] = mapped_column(String, nullable=False, unique=True)