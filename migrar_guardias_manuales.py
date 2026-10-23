from sqlalchemy import text

from database import engine


def migrar_guardias_manuales():
    """
    Migra la tabla antigua de guardias por frecuencia a guardias manuales.

    IMPORTANTE: por decisión administrativa, las guardias antiguas NO se
    convierten a fechas manuales. Se eliminan para que el administrador
    vuelva a marcar los días reales desde el perfil de cada médico.
    """
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))

        # Tablas nuevas para grupos Artículo 8.
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grupos_articulo8 (
                id_grupo INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(120) NOT NULL UNIQUE,
                fecha_registro DATETIME,
                fecha_actualizacion DATETIME
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grupos_articulo8_medicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_grupo INTEGER NOT NULL,
                id_medico INTEGER NOT NULL,
                CONSTRAINT uq_grupo_art8_medico
                    UNIQUE (id_grupo, id_medico),
                FOREIGN KEY (id_grupo)
                    REFERENCES grupos_articulo8(id_grupo),
                FOREIGN KEY (id_medico)
                    REFERENCES medicos(id_medico)
            )
        """))

        columnas = [
            fila[1]
            for fila in conn.execute(
                text("PRAGMA table_info(guardias)")
            ).fetchall()
        ]

        if "fecha_guardia" not in columnas:
            # La tabla anterior tenía fecha_inicio/frecuencia_dias como
            # NOT NULL. Se reconstruye para que esos campos sean opcionales
            # y cada guardia pueda representar un día individual.
            conn.execute(text("""
                CREATE TABLE guardias_nueva (
                    id_guardia INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_medico INTEGER NOT NULL,
                    fecha_guardia DATE,
                    fecha_inicio DATE,
                    frecuencia_dias INTEGER,
                    fecha_fin DATE,
                    activo BOOLEAN DEFAULT 1,
                    observacion VARCHAR(255),
                    id_grupo_articulo8 INTEGER,
                    FOREIGN KEY (id_medico)
                        REFERENCES medicos(id_medico),
                    FOREIGN KEY (id_grupo_articulo8)
                        REFERENCES grupos_articulo8(id_grupo)
                )
            """))

            # NO se copian los registros antiguos: el usuario solicitó
            # comenzar de cero y reasignar manualmente las guardias.
            conn.execute(text("DROP TABLE guardias"))
            conn.execute(text("ALTER TABLE guardias_nueva RENAME TO guardias"))

        conn.execute(text("PRAGMA foreign_keys=ON"))


if __name__ == "__main__":
    migrar_guardias_manuales()
    print("Migración de guardias manuales completada.")
