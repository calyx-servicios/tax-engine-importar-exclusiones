"""Models for ORM"""
# pylint: disable=unused-import
from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint

from app.model.database import Base


class Arba(Base):
    """Arba"""

    __tablename__ = "arba_padron_general"
    __table_args__ = ({"postgresql_partition_by": "LIST (periodo)"},)
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime)
    periodo = Column(String, primary_key=True)
    nro_grupo_percepcion = Column(String)
    fecha_publicacion = Column(DateTime)
    fecha_desde = Column(DateTime)
    fecha_hasta = Column(DateTime)
    cuit = Column(String)
    tipo_contr_insc = Column(String)
    marca_alta_sujeto = Column(String)
    marca_cambio_alicuota = Column(String)
    alicuota_percepcion = Column(Float)
    alicuota_retencion = Column(Float)
