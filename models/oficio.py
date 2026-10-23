from models.base import Base

from sqlalchemy import (
    Column,
    Integer,
    Date,
    String,
    Text,
    DateTime,
    func
)


class Oficio(Base):
    """
    Representa cada renglón del libro de control de oficios
    (el cuaderno físico: N°, Fecha, Destinatario, Asunto),
    más el campo adicional de Observación que se agrega
    a la versión digital.
    """

    __tablename__ = "oficios"

    id_oficio = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Número correlativo del oficio tal como se lleva en el
    # cuaderno (ej: "086", "087"...). Se guarda como texto para
    # respetar los ceros a la izquierda, pero es único.
    numero = Column(
        String(20),
        nullable=False,
        unique=True
    )

    fecha = Column(
        Date,
        nullable=False
    )

    destinatario = Column(
        Text,
        nullable=False
    )

    asunto = Column(
        Text,
        nullable=False
    )

    # Campo NUEVO solicitado, no existe en el cuaderno físico.
    observacion = Column(
        Text,
        nullable=True
    )

    fecha_registro = Column(
        DateTime,
        server_default=func.now()
    )
