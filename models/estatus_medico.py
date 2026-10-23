from models.base import Base
from sqlalchemy import Column, Integer, String


class EstatusMedico(Base):

    __tablename__ = "estatus_medico"

    id_estatus = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre = Column(
        String(100),
        nullable=False
    )