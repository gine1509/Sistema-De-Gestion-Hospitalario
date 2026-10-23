from database import engine
from models.base import Base
from models.medico import Medico
from models.guardia import Guardia
from models.dependencia import Dependencia
from models.tipo_contratacion import TipoContratacion
from models.estatus_medico import EstatusMedico
from models.oficio import Oficio
from models.personal_direccion import PersonalDireccion, HorarioDireccion
from models.usuarios import Usuario
from sqlalchemy import text

# 1. Crear las tablas principales
Base.metadata.create_all(bind=engine)

# 1.1 Crear el usuario administrador inicial (si no existe)
from services.usuario_service import asegurar_usuario_admin
asegurar_usuario_admin()

# 2. Crear la vista SQL personalizada
sql_crear_vista = """
CREATE VIEW IF NOT EXISTS vw_medicos_completo AS
SELECT
    m.id_medico,
    m.codigo,
    m.cedula,
    m.nombres,
    m.apellidos,
    m.telefono,
    m.correo,
    m.cargo,
    m.especialidad,
    d.nombre AS dependencia,
    tc.nombre AS tipo_contratacion,
    m.centro_salud,
    m.asic,
    m.tipologia_centro,
    m.ubicacion_administrativa,
    e.nombre AS estatus,
    m.causa_inactividad,
    m.formacion_estudiando,
    m.fecha_ingreso
FROM medicos m
LEFT JOIN dependencias d ON d.id_dependencia = m.id_dependencia
LEFT JOIN tipos_contratacion tc ON tc.id_tipo_contratacion = m.id_tipo_contratacion
LEFT JOIN estatus_medico e ON e.id_estatus = m.id_estatus;
"""

# 3. Corregir la cédula del administrador existente
sql_actualizar_admin = """
UPDATE usuarios 
SET cedula = 'V-12345678' 
WHERE usuario = 'admin';
"""

with engine.connect() as conn:
    conn.execute(text(sql_crear_vista))
    conn.execute(text(sql_actualizar_admin))
    conn.commit()  # Necesario en versiones recientes de SQLAlchemy para guardar el UPDATE

print("Base de datos actualizada, vista SQL creada y cédula del administrador corregida.")