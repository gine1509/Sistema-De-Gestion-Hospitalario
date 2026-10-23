from models.base import Base

from sqlalchemy import (
    Column,
    Integer,
    Date,
    Boolean,
    ForeignKey,
    String
)


class Guardia(Base):
    """
    Guardia manual: cada registro representa un día concreto asignado
    a un médico. Los campos de frecuencia se conservan únicamente para
    compatibilidad con bases antiguas, pero ya no participan en la lógica.
    """

    __tablename__ = "guardias"

    id_guardia = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_medico = Column(
        Integer,
        ForeignKey("medicos.id_medico"),
        nullable=False
    )

    # NUEVA LÓGICA: un registro = un día de guardia.
    fecha_guardia = Column(
        Date,
        nullable=True
    )

    # Campos antiguos conservados para no romper bases existentes.
    fecha_inicio = Column(
        Date,
        nullable=True
    )

    frecuencia_dias = Column(
        Integer,
        nullable=True
    )

    fecha_fin = Column(
        Date,
        nullable=True
    )

    activo = Column(
        Boolean,
        default=True
    )

    observacion = Column(
        String(255),
        nullable=True
    )

    # Grupo Artículo 8 al que pertenece esta asignación, si aplica.
    id_grupo_articulo8 = Column(
        Integer,
        ForeignKey("grupos_articulo8.id_grupo"),
        nullable=True
    )
