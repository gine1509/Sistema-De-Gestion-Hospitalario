from models.base import Base

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint
)


class GrupoArticulo8Medico(Base):

    __tablename__ = "grupos_articulo8_medicos"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_grupo = Column(
        Integer,
        ForeignKey("grupos_articulo8.id_grupo"),
        nullable=False
    )

    id_medico = Column(
        Integer,
        ForeignKey("medicos.id_medico"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "id_grupo",
            "id_medico",
            name="uq_grupo_art8_medico"
        ),
    )
