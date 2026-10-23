from datetime import datetime, date

from sqlalchemy import text

from database import SessionLocal
from models.medico import Medico
from models.dependencia import Dependencia
from models.tipo_contratacion import TipoContratacion
from models.estatus_medico import EstatusMedico
from models.guardia import Guardia
from models.grupo_articulo8_medico import GrupoArticulo8Medico


# ============================================================
# UTILIDADES
# ============================================================

def _valor_o_none(valor):
    """
    Convierte cadenas vacías en None.
    """
    if valor is None:
        return None

    if isinstance(valor, str):
        valor = valor.strip()

        if valor == "":
            return None

    return valor


# ============================================================
# LISTAR MÉDICOS
# ============================================================

def listar_medicos():
    """
    Devuelve todos los médicos utilizando la vista
    vw_medicos_completo.

    Se utiliza principalmente para:
    - VistaMedicos
    - tarjetas
    - búsqueda
    - filtros
    """

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                v.id_medico,
                v.codigo,
                v.cedula,
                v.nombres,
                v.apellidos,
                v.telefono,
                v.correo,
                v.cargo,
                v.especialidad,
                v.dependencia,
                v.tipo_contratacion,
                v.centro_salud,
                v.asic,
                v.tipologia_centro,
                v.ubicacion_administrativa,
                v.estatus,
                v.causa_inactividad,
                m.fecha_inicio_inactividad,
                m.fecha_fin_inactividad,
                m.tiempo_inactividad,
                v.formacion_estudiando,
                v.fecha_ingreso
            FROM vw_medicos_completo v
            LEFT JOIN medicos m
                ON m.id_medico = v.id_medico
            ORDER BY v.id_medico DESC
        """)

        resultado = db.execute(query)

        filas = resultado.mappings().all()
        
        medicos = []

        for fila in filas:
            # MOVIDO ADENTRO DEL BUCLE
            nombres = (fila["nombres"] or "").strip()
            apellidos = (fila["apellidos"] or "").strip()
            nombre_completo = f"{nombres} {apellidos}".strip()

            medicos.append({
                "id_medico": fila["id_medico"],
                "codigo": fila["codigo"] or "",
                "nombre": nombre_completo,
                "nombres": nombres,
                "apellidos": apellidos,
                "cedula": fila["cedula"] or "",
                "telefono": fila["telefono"] or "",
                "correo": fila["correo"] or "",
                "cargo": fila["cargo"] or "",
                "especialidad": fila["especialidad"] or "",
                "dependencia": fila["dependencia"] or "",
                "contratacion": (
                    fila["tipo_contratacion"] or ""
                ),
                "centro": fila["centro_salud"] or "",
                "asic": fila["asic"] or "",
                "tipologia_centro": (
                    fila["tipologia_centro"] or ""
                ),
                "ubicacion": (
                    fila["ubicacion_administrativa"] or ""
                ),
                "formacion": (
                    fila["formacion_estudiando"] or ""
                ),
                "estatus": fila["estatus"] or "",
                "causa_inactividad": (
                    fila["causa_inactividad"] or ""
                ),
                "fecha_inicio_inactividad": fila["fecha_inicio_inactividad"],
                "fecha_fin_inactividad": fila["fecha_fin_inactividad"],
                "tiempo_inactividad": fila["tiempo_inactividad"],
                "fecha_ingreso": fila["fecha_ingreso"],
            })

        return medicos

    finally:
        db.close()
        
# ============================================================
# ESTADÍSTICAS DE MÉDICOS
# ============================================================

def obtener_estadisticas_medicos():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                COUNT(*) AS total,

                SUM(
                    CASE
                        WHEN UPPER(TRIM(estatus)) = 'ACTIVO'
                        THEN 1
                        ELSE 0
                    END
                ) AS activos,

                SUM(
                    CASE
                        WHEN UPPER(TRIM(estatus)) = 'INACTIVO'
                        THEN 1
                        ELSE 0
                    END
                ) AS inactivos,

                SUM(
                    CASE
                        WHEN especialidad IS NOT NULL
                             AND TRIM(especialidad) <> ''
                        THEN 1
                        ELSE 0
                    END
                ) AS especialistas,

                SUM(
                    CASE
                        WHEN UPPER(TRIM(cargo)) = 'ARTICULO 8'
                        THEN 1
                        ELSE 0
                    END
                ) AS art8

            FROM vw_medicos_completo
        """)

        resultado = db.execute(query).mappings().first()

        return {
            "total": resultado["total"] or 0,
            "activos": resultado["activos"] or 0,
            "inactivos": resultado["inactivos"] or 0,
            "especialistas": resultado["especialistas"] or 0,
            "art8": resultado["art8"] or 0
        }

    except Exception as e:
        print(
            f"[EstadisticasMedicos] Error: {e}"
        )

        return {
            "total": 0,
            "activos": 0,
            "inactivos": 0,
            "especialistas": 0,
            "art8": 0
        }

    finally:
        db.close()


# ============================================================
# BUSCAR POR CÉDULA
# ============================================================

def buscar_por_cedula(cedula):

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                id_medico,
                codigo,
                cedula,
                nombres,
                apellidos,
                telefono,
                correo,
                cargo,
                especialidad,
                dependencia,
                tipo_contratacion,
                centro_salud,
                asic,
                tipologia_centro,
                ubicacion_administrativa,
                estatus,
                causa_inactividad,
                formacion_estudiando,
                fecha_ingreso
            FROM vw_medicos_completo
            WHERE cedula = :cedula
            LIMIT 1
        """)

        resultado = db.execute(
            query,
            {
                "cedula": cedula
            }
        )

        fila = resultado.mappings().first()

        if not fila:
            return None

        return dict(fila)

    finally:
        db.close()


# ============================================================
# OBTENER MÉDICO POR ID
# ============================================================

def obtener_medico(id_medico):

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                m.id_medico,
                m.codigo,
                m.cedula,
                m.nombres,
                m.apellidos,
                m.telefono,
                m.correo,

                m.id_dependencia,
                d.nombre AS dependencia,

                m.id_tipo_contratacion,
                tc.nombre AS tipo_contratacion,

                m.ubicacion_administrativa,

                m.id_estatus,
                e.nombre AS estatus,

                m.formacion_estudiando,
                m.fecha_ingreso,
                m.fecha_registro,
                m.fecha_actualizacion,

                m.cargo,
                m.especialidad,
                m.centro_salud,
                m.asic,
                m.tipologia_centro,
                m.causa_inactividad,
                
                m.fecha_inicio_inactividad,
                m.fecha_fin_inactividad,
                m.tiempo_inactividad

            FROM medicos m

            LEFT JOIN dependencias d
                ON d.id_dependencia = m.id_dependencia

            LEFT JOIN tipos_contratacion tc
                ON tc.id_tipo_contratacion =
                   m.id_tipo_contratacion

            LEFT JOIN estatus_medico e
                ON e.id_estatus = m.id_estatus

            -- 👇 NUEVA RELACIÓN AGREGADA

            WHERE m.id_medico = :id_medico

            LIMIT 1
        """)

        resultado = db.execute(
            query,
            {
                "id_medico": id_medico
            }
        )

        fila = resultado.mappings().first()

        if not fila:
            return None

        return dict(fila)

    finally:
        db.close()


# ============================================================
# CREAR MÉDICO
# ============================================================

def crear_medico(datos):

    db = SessionLocal()

    try:

        cedula = _valor_o_none(datos.get("cedula"))

        # ----------------------------------------------------
        # Verificar cédula
        # ----------------------------------------------------

        existente = db.query(Medico).filter(
            Medico.cedula == cedula
        ).first()

        if existente:

            return {
                "ok": False,
                "mensaje": "Ya existe un médico con esa cédula."
            }

        # ----------------------------------------------------
        # Validar dependencia
        # ----------------------------------------------------

        id_dependencia = _valor_o_none(
            datos.get("id_dependencia")
        )

        if id_dependencia is not None:

            dependencia = db.query(
                Dependencia
            ).filter(
                Dependencia.id_dependencia ==
                id_dependencia
            ).first()

            if not dependencia:

                return {
                    "ok": False,
                    "mensaje": "La dependencia seleccionada no existe."
                }

        # ----------------------------------------------------
        # Validar contratación
        # ----------------------------------------------------

        id_tipo_contratacion = _valor_o_none(
            datos.get("id_tipo_contratacion")
        )

        if id_tipo_contratacion is not None:

            contratacion = db.query(
                TipoContratacion
            ).filter(
                TipoContratacion.id_tipo_contratacion ==
                id_tipo_contratacion
            ).first()

            if not contratacion:

                return {
                    "ok": False,
                    "mensaje": (
                        "El tipo de contratación "
                        "seleccionado no existe."
                    )
                }

        # ----------------------------------------------------
        # Crear objeto
        # ----------------------------------------------------

        medico = Medico(

            cedula=cedula,

            codigo=_valor_o_none(
                datos.get("codigo")
            ),

            nombres=datos.get(
                "nombres",
                ""
            ).strip().upper(),

            apellidos=datos.get(
                "apellidos",
                ""
            ).strip().upper(),

            telefono=_valor_o_none(
                datos.get("telefono")
            ),

            correo=_valor_o_none(
                datos.get("correo")
            ),

            id_dependencia=id_dependencia,

            id_tipo_contratacion=id_tipo_contratacion,

            ubicacion_administrativa=_valor_o_none(
                datos.get("ubicacion_administrativa")
            ),

            id_estatus=datos.get(
                "id_estatus"
            ) or 1,

            formacion_estudiando=_valor_o_none(
                datos.get("formacion_estudiando")
            ),

            fecha_ingreso=datos.get(
                "fecha_ingreso"
            ),

            fecha_registro=datetime.now(),

            fecha_actualizacion=datetime.now(),

            cargo=_valor_o_none(
                datos.get("cargo")
            ),

            especialidad=_valor_o_none(
                datos.get("especialidad")
            ),

            centro_salud=_valor_o_none(
                datos.get("centro_salud")
            ),

            asic=_valor_o_none(
                datos.get("asic")
            ),

            tipologia_centro=_valor_o_none(
                datos.get("tipologia_centro")
            ),

            causa_inactividad=_valor_o_none(
                datos.get("causa_inactividad")
            ),
            
            fecha_inicio_inactividad=
                datos.get("fecha_inicio_inactividad"),

            fecha_fin_inactividad=
                datos.get("fecha_fin_inactividad"),

            tiempo_inactividad=
                _valor_o_none(
                    datos.get("tiempo_inactividad")
                ),
        )

        db.add(medico)

        db.flush()
        db.commit()

        db.refresh(medico)

        return {
            "ok": True,
            "mensaje": "Médico registrado correctamente.",
            "id_medico": medico.id_medico
        }

    except Exception as e:

        db.rollback()

        return {
            "ok": False,
            "mensaje": f"Error al registrar médico: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# EDITAR MÉDICO
# ============================================================

def actualizar_medico(id_medico, datos):

    db = SessionLocal()

    try:

        medico = db.query(
            Medico
        ).filter(
            Medico.id_medico == id_medico
        ).first()

        if not medico:

            return {
                "ok": False,
                "mensaje": "El médico no existe."
            }

        # ----------------------------------------------------
        # Cédula
        # ----------------------------------------------------

        nueva_cedula = _valor_o_none(
            datos.get("cedula")
        )

        if nueva_cedula and nueva_cedula != medico.cedula:

            duplicado = db.query(
                Medico
            ).filter(
                Medico.cedula == nueva_cedula,
                Medico.id_medico != id_medico
            ).first()

            if duplicado:

                return {
                    "ok": False,
                    "mensaje": (
                        "La nueva cédula ya pertenece "
                        "a otro médico."
                    )
                }

            medico.cedula = nueva_cedula

        # ----------------------------------------------------
        # Campos personales
        # ----------------------------------------------------

        if "codigo" in datos:
            medico.codigo = _valor_o_none(
                datos.get("codigo")
            )

        if "nombres" in datos:
            medico.nombres = datos.get(
                "nombres",
                ""
            ).strip().upper()

        if "apellidos" in datos:
            medico.apellidos = datos.get(
                "apellidos",
                ""
            ).strip().upper()

        if "telefono" in datos:
            medico.telefono = _valor_o_none(
                datos.get("telefono")
            )

        if "correo" in datos:
            medico.correo = _valor_o_none(
                datos.get("correo")
            )

        # ----------------------------------------------------
        # Datos administrativos
        # ----------------------------------------------------

        if "id_dependencia" in datos:

            id_dependencia = _valor_o_none(
                datos.get("id_dependencia")
            )

            if id_dependencia is not None:

                dependencia = db.query(
                    Dependencia
                ).filter(
                    Dependencia.id_dependencia ==
                    id_dependencia
                ).first()

                if not dependencia:

                    return {
                        "ok": False,
                        "mensaje": (
                            "La dependencia "
                            "seleccionada no existe."
                        )
                    }

            medico.id_dependencia = id_dependencia

        # ----------------------------------------------------
        # Contratación
        # ----------------------------------------------------

        if "id_tipo_contratacion" in datos:

            id_contratacion = _valor_o_none(
                datos.get("id_tipo_contratacion")
            )

            if id_contratacion is not None:

                contratacion = db.query(
                    TipoContratacion
                ).filter(
                    TipoContratacion
                    .id_tipo_contratacion ==
                    id_contratacion
                ).first()

                if not contratacion:

                    return {
                        "ok": False,
                        "mensaje": (
                            "El tipo de contratación "
                            "seleccionado no existe."
                        )
                    }

            medico.id_tipo_contratacion = (
                id_contratacion
            )

        if "ubicacion_administrativa" in datos:

            medico.ubicacion_administrativa = (
                _valor_o_none(
                    datos.get(
                        "ubicacion_administrativa"
                    )
                )
            )

        # ----------------------------------------------------
        # Estado
        # ----------------------------------------------------

        if "id_estatus" in datos:

            id_estatus = datos.get(
                "id_estatus"
            )

            if id_estatus is not None:

                estatus = db.query(
                    EstatusMedico
                ).filter(
                    EstatusMedico.id_estatus ==
                    id_estatus
                ).first()

                if not estatus:

                    return {
                        "ok": False,
                        "mensaje": (
                            "El estatus seleccionado "
                            "no existe."
                        )
                    }

                medico.id_estatus = id_estatus

        # ----------------------------------------------------
        # Formación
        # ----------------------------------------------------

        if "formacion_estudiando" in datos:

            medico.formacion_estudiando = (
                _valor_o_none(
                    datos.get(
                        "formacion_estudiando"
                    )
                )
            )

        # ----------------------------------------------------
        # Fecha de ingreso
        # ----------------------------------------------------

        if "fecha_ingreso" in datos:

            medico.fecha_ingreso = (
                datos.get("fecha_ingreso")
            )

        # ----------------------------------------------------
        # Información profesional
        # ----------------------------------------------------

        if "cargo" in datos:

            medico.cargo = _valor_o_none(
                datos.get("cargo")
            )

        if "especialidad" in datos:

            medico.especialidad = _valor_o_none(
                datos.get("especialidad")
            )

        if "centro_salud" in datos:

            medico.centro_salud = _valor_o_none(
                datos.get("centro_salud")
            )

        if "asic" in datos:

            medico.asic = _valor_o_none(
                datos.get("asic")
            )

        if "tipologia_centro" in datos:

            medico.tipologia_centro = _valor_o_none(
                datos.get("tipologia_centro")
            )

        # ----------------------------------------------------
        # Causa de inactividad
        # ----------------------------------------------------

        if "causa_inactividad" in datos:

            medico.causa_inactividad = (
                _valor_o_none(
                    datos.get(
                        "causa_inactividad"
                    )
                )
            )
        
        # --- FALTABA ACTUALIZAR ESTOS CAMPOS DE INACTIVIDAD ---
        if "fecha_inicio_inactividad" in datos:
            medico.fecha_inicio_inactividad = datos.get("fecha_inicio_inactividad")
        if "fecha_fin_inactividad" in datos:
            medico.fecha_fin_inactividad = datos.get("fecha_fin_inactividad")
        if "tiempo_inactividad" in datos:
            medico.tiempo_inactividad = _valor_o_none(datos.get("tiempo_inactividad"))
        # ----------------------------------------------------
        # Actualizar fecha
        # ----------------------------------------------------

        medico.fecha_actualizacion = datetime.now()

        db.commit()

        db.refresh(medico)

        return {
            "ok": True,
            "mensaje": "Médico actualizado correctamente.",
            "id_medico": medico.id_medico
        }

    except Exception as e:

        db.rollback()

        return {
            "ok": False,
            "mensaje": f"Error al actualizar médico: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# DESACTIVAR MÉDICO
# ============================================================

def desactivar_medico(id_medico):

    db = SessionLocal()

    try:

        medico = db.query(
            Medico
        ).filter(
            Medico.id_medico == id_medico
        ).first()

        if not medico:

            return {
                "ok": False,
                "mensaje": "El médico no existe."
            }

        medico.id_estatus = 2

        medico.fecha_actualizacion = datetime.now()

        db.commit()

        return {
            "ok": True,
            "mensaje": "Médico desactivado correctamente."
        }

    except Exception as e:

        db.rollback()

        return {
            "ok": False,
            "mensaje": f"Error al desactivar médico: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# REACTIVAR MÉDICO
# ============================================================

def activar_medico(id_medico):

    db = SessionLocal()

    try:

        medico = db.query(
            Medico
        ).filter(
            Medico.id_medico == id_medico
        ).first()

        if not medico:

            return {
                "ok": False,
                "mensaje": "El médico no existe."
            }

        medico.id_estatus = 1

        medico.causa_inactividad = None

        medico.fecha_actualizacion = datetime.now()

        db.commit()

        return {
            "ok": True,
            "mensaje": "Médico activado correctamente."
        }

    except Exception as e:

        db.rollback()

        return {
            "ok": False,
            "mensaje": f"Error al activar médico: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# ELIMINACIÓN FÍSICA
# ============================================================

def eliminar_medico(id_medico):
    db = SessionLocal()
    try:
        medico = db.query(Medico).filter(Medico.id_medico == id_medico).first()

        if not medico:
            return {
                "ok": False,
                "mensaje": "El médico no existe."
            }

        # 1. Eliminar todas las guardias manuales asociadas al médico
        db.query(Guardia).filter(
            Guardia.id_medico == id_medico
        ).delete(synchronize_session=False)

        # 2. Eliminar la pertenencia a grupos Artículo 8
        db.query(GrupoArticulo8Medico).filter(
            GrupoArticulo8Medico.id_medico == id_medico
        ).delete(synchronize_session=False)

        # 3. Eliminar el registro del médico
        db.delete(medico)

        db.commit()

        return {
            "ok": True,
            "mensaje": "Médico y toda su información asociada eliminados correctamente."
        }

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "mensaje": f"No se pudo eliminar el médico: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# CATÁLOGOS
# ============================================================

def listar_dependencias():

    db = SessionLocal()

    try:

        resultados = db.query(
            Dependencia
        ).order_by(
            Dependencia.nombre
        ).all()

        return [
            {
                "id_dependencia": item.id_dependencia,
                "nombre": item.nombre
            }
            for item in resultados
        ]

    finally:
        db.close()


def listar_tipos_contratacion():

    db = SessionLocal()

    try:

        resultados = db.query(
            TipoContratacion
        ).order_by(
            TipoContratacion.nombre
        ).all()

        return [
            {
                "id_tipo_contratacion":
                    item.id_tipo_contratacion,
                "nombre": item.nombre
            }
            for item in resultados
        ]

    finally:
        db.close()


def listar_estatus():

    db = SessionLocal()

    try:

        resultados = db.query(
            EstatusMedico
        ).order_by(
            EstatusMedico.id_estatus
        ).all()

        return [
            {
                "id_estatus": item.id_estatus,
                "nombre": item.nombre
            }
            for item in resultados
        ]

    finally:
        db.close()
        
# ============================================================
# FILTROS DINÁMICOS
# ============================================================

def listar_cargos():
    db = SessionLocal()
    try:
        query = text("""
            SELECT DISTINCT cargo 
            FROM vw_medicos_completo 
            WHERE cargo IS NOT NULL AND TRIM(cargo) <> ''
            ORDER BY cargo
        """)
        resultados = db.execute(query).fetchall()
        return [row[0] for row in resultados]
    except Exception as e:
        print(f"[Filtros] Error obteniendo cargos: {e}")
        return []
    finally:
        db.close()

def listar_centros():
    db = SessionLocal()
    try:
        query = text("""
            SELECT DISTINCT centro_salud 
            FROM vw_medicos_completo 
            WHERE centro_salud IS NOT NULL AND TRIM(centro_salud) <> ''
            ORDER BY centro_salud
        """)
        resultados = db.execute(query).fetchall()
        return [row[0] for row in resultados]
    except Exception as e:
        print(f"[Filtros] Error obteniendo centros: {e}")
        return []
    finally:
        db.close()