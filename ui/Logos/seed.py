from database import SessionLocal
from models.dependencia import Dependencia
from models.tipo_contratacion import TipoContratacion
from models.estatus_medico import EstatusMedico

def sembrar_datos():
    db = SessionLocal()
    try:
        # 1. Estatus
        estatus_iniciales = [
            (1, "ACTIVO"),
            (2, "INACTIVO")
        ]
        for id_est, nombre in estatus_iniciales:
            if not db.query(EstatusMedico).filter_by(id_estatus=id_est).first():
                db.add(EstatusMedico(id_estatus=id_est, nombre=nombre))

        # 2. Dependencias
        dependencias_iniciales = [
            (1, "MPPS"),
            (2, "CORPOSALUD")
        ]
        for id_dep, nombre in dependencias_iniciales:
            if not db.query(Dependencia).filter_by(id_dependencia=id_dep).first():
                db.add(Dependencia(id_dependencia=id_dep, nombre=nombre))

        # 3. Tipos de Contratación
        contrataciones_iniciales = [
            (1, "FIJO"),
            (2, "CONTRATADO")
        ]
        for id_tc, nombre in contrataciones_iniciales:
            if not db.query(TipoContratacion).filter_by(id_tipo_contratacion=id_tc).first():
                db.add(TipoContratacion(id_tipo_contratacion=id_tc, nombre=nombre))

        db.commit()
        print("¡Catálogos registrados con éxito en SQLite!")
    except Exception as e:
        db.rollback()
        print(f"Error al sembrar datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    sembrar_datos()
    
    
   