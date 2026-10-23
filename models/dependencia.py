from models.base import Base
from sqlalchemy import Column, Integer, String


class Dependencia(Base):

    __tablename__ = "dependencias"

    id_dependencia = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre = Column(
        String(100),
        nullable=False
    )