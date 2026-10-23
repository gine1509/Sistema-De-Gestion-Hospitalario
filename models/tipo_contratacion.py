from models.base import Base
from sqlalchemy import Column, Integer, String


class TipoContratacion(Base):

    __tablename__ = "tipos_contratacion"

    id_tipo_contratacion = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre = Column(
        String(100),
        nullable=False
    )