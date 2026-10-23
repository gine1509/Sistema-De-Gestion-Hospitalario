from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from models.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    cedula = Column(String(20), nullable=False, unique=True)
    usuario = Column(String(50), nullable=False, unique=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="secretaria")  # "admin" | "secretaria"
    activo = Column(Boolean, nullable=False, default=True)

    fecha_registro = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
