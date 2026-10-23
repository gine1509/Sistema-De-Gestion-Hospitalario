from models.base import Base

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)


class GrupoArticulo8(Base):

    __tablename__ = "grupos_articulo8"

    id_grupo = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre = Column(
        String(120),
        nullable=False,
        unique=True
    )

    fecha_registro = Column(
        DateTime,
        nullable=True
    )

    fecha_actualizacion = Column(
        DateTime,
        nullable=True
    )
