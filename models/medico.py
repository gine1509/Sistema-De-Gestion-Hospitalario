from models.base import Base

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime
)


class Medico(Base):

    __tablename__ = "medicos"

    id_medico = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    cedula = Column(
        String(15),
        nullable=False,
        unique=True
    )

    codigo = Column(
        String(50),
        nullable=True
    )

    nombres = Column(
        String(100),
        nullable=False
    )

    apellidos = Column(
        String(100),
        nullable=False
    )

    telefono = Column(
        String(50),
        nullable=True
    )

    correo = Column(
        String(120),
        nullable=True
    )

    id_dependencia = Column(
        Integer,
        nullable=True
    )

    id_tipo_contratacion = Column(
        Integer,
        nullable=True
    )

    ubicacion_administrativa = Column(
        String(150),
        nullable=True
    )

    id_estatus = Column(
        Integer,
        nullable=False,
        default=1
    )

    formacion_estudiando = Column(
        String(120),
        nullable=True
    )

    fecha_ingreso = Column(
        Date,
        nullable=True
    )

    fecha_registro = Column(
        DateTime,
        nullable=True
    )

    fecha_actualizacion = Column(
        DateTime,
        nullable=True
    )

    cargo = Column(
        String(150),
        nullable=True
    )

    especialidad = Column(
        String(150),
        nullable=True
    )

    centro_salud = Column(
        String(200),
        nullable=True
    )

    asic = Column(
        String(150),
        nullable=True
    )

    tipologia_centro = Column(
        String(150),
        nullable=True
    )

    causa_inactividad = Column(
        String(255),
        nullable=True
    )
    
    fecha_inicio_inactividad = Column(
        Date,
        nullable=True
    )

    fecha_fin_inactividad = Column(
        Date,
        nullable=True
    )

    tiempo_inactividad = Column(
        String(100),
        nullable=True
    )