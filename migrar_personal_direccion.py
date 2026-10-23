"""
Migración: agrega a la tabla `personal_direccion` las columnas necesarias
para registrar la inactividad del personal de dirección
(causa, fecha inicio, fecha fin y tiempo calculado).

Es seguro ejecutar este script más de una vez: si una columna ya existe,
simplemente se omite.

Uso:
    python migrar_personal_direccion.py
"""

from sqlalchemy import text
from database import engine

COLUMNAS_NUEVAS = {
    "causa_inactividad": "VARCHAR(255)",
    "fecha_inicio_inactividad": "DATE",
    "fecha_fin_inactividad": "DATE",
    "tiempo_inactividad": "VARCHAR(100)",
}


def columnas_existentes(conn):
    resultado = conn.execute(text("PRAGMA table_info(personal_direccion)"))
    return {fila[1] for fila in resultado.fetchall()}


def migrar():
    with engine.connect() as conn:
        existentes = columnas_existentes(conn)

        for columna, tipo in COLUMNAS_NUEVAS.items():
            if columna in existentes:
                print(f"- La columna '{columna}' ya existe. Se omite.")
                continue

            conn.execute(
                text(f"ALTER TABLE personal_direccion ADD COLUMN {columna} {tipo}")
            )
            print(f"+ Columna '{columna}' agregada correctamente.")

        conn.commit()

    print("Migración completada.")


if __name__ == "__main__":
    migrar()
