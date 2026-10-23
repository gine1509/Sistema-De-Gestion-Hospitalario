from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from models.base import Base


class PersonalDireccion(Base):
    __tablename__ = "personal_direccion"

    id_personal = Column(Integer, primary_key=True, autoincrement=True)
    cedula = Column(String(20), nullable=False, unique=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    telefono = Column(String(50), nullable=True)
    correo = Column(String(120), nullable=True)
    cargo = Column(String(120), nullable=True)
    fecha_ingreso = Column(Date, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    observacion = Column(String(255), nullable=True)

    causa_inactividad = Column(String(255), nullable=True)
    fecha_inicio_inactividad = Column(Date, nullable=True)
    fecha_fin_inactividad = Column(Date, nullable=True)
    tiempo_inactividad = Column(String(100), nullable=True)

    fecha_registro = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HorarioDireccion(Base):
    __tablename__ = "horarios_direccion"

    id_horario = Column(Integer, primary_key=True, autoincrement=True)
    id_personal = Column(Integer, nullable=False)
    dia_semana = Column(Integer, nullable=False)  # 1=Lunes ... 7=Domingo
    hora_entrada = Column(String(10), nullable=False)
    hora_salida = Column(String(10), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
