import unicodedata
from datetime import date, datetime, timedelta

from database import SessionLocal
from models.guardia import Guardia
from models.medico import Medico
from models.grupo_articulo8 import GrupoArticulo8
from models.grupo_articulo8_medico import GrupoArticulo8Medico


# ============================================================
# UTILIDADES
# ============================================================

def _convertir_fecha(valor):
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        valor = valor.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                pass

    return None


def _medico_inactivo_en_fecha(medico, fecha):
    inicio = _convertir_fecha(medico.fecha_inicio_inactividad)
    fin = _convertir_fecha(medico.fecha_fin_inactividad)

    if inicio and fin:
        return inicio <= fecha <= fin

    if inicio:
        return fecha >= inicio

    if fin:
        return fecha <= fin

    return False


def _normalizar_texto(texto):
    texto = (texto or "").strip().lower()
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def _causa_es_definitiva(causa):
    causa = _normalizar_texto(causa)
    return "renunci" in causa or "jubil" in causa


def _tiene_inactividad_configurada(medico):
    return (
        _convertir_fecha(medico.fecha_inicio_inactividad) is not None
        or _convertir_fecha(medico.fecha_fin_inactividad) is not None
    )


def _inactividad_se_solapa_con_mes(
    fecha_inicio_inactividad,
    fecha_fin_inactividad,
    fecha_inicio_mes,
    fecha_fin_mes,
    es_definitiva=False
):
    if es_definitiva:
        return bool(
            fecha_inicio_inactividad
            and fecha_inicio_mes <= fecha_inicio_inactividad <= fecha_fin_mes
        )

    inicio_ok = (
        fecha_fin_inactividad is None
        or fecha_fin_inactividad >= fecha_inicio_mes
    )
    fin_ok = (
        fecha_inicio_inactividad is None
        or fecha_inicio_inactividad <= fecha_fin_mes
    )
    return inicio_ok and fin_ok


def _cargos_normalizados(cargo):
    """Acepta el cargo antiguo en texto o una lista/tupla de cargos."""
    if cargo is None:
        return []

    if isinstance(cargo, (list, tuple, set)):
        valores = cargo
    else:
        valores = [cargo]

    resultado = []
    for valor in valores:
        valor = str(valor or "").strip()
        if valor and _normalizar_texto(valor) not in (
            "todos los cargos",
            "todos",
        ):
            resultado.append(_normalizar_texto(valor))

    return resultado


def _es_articulo_8(medico):
    return _normalizar_texto(medico.cargo) == "articulo 8"


def _es_interno(medico):
    cargo = _normalizar_texto(medico.cargo)
    return "intern" in cargo

def _es_elegible_grupo(medico):
    """Un grupo Artículo 8 puede contener médicos Artículo 8 o Internos."""
    return _es_articulo_8(medico) or _es_interno(medico)


# ============================================================
# GUARDIAS MANUALES DEL MÉDICO
# ============================================================

def obtener_guardias_medico(id_medico):
    db = SessionLocal()
    try:
        registros = (
            db.query(Guardia)
            .filter(
                Guardia.id_medico == id_medico,
                Guardia.activo == True
            )
            .order_by(Guardia.fecha_guardia.asc(), Guardia.id_guardia.asc())
            .all()
        )

        return [
            {
                "id_guardia": g.id_guardia,
                "id_medico": g.id_medico,
                "fecha_guardia": _convertir_fecha(g.fecha_guardia),
                "id_grupo_articulo8": g.id_grupo_articulo8,
                "observacion": g.observacion or "",
            }
            for g in registros
            if _convertir_fecha(g.fecha_guardia)
        ]
    finally:
        db.close()


def guardar_guardias_medico(
    id_medico,
    fechas,
    id_grupo_articulo8=None
):
    """
    Reemplaza las guardias manuales del médico por las fechas recibidas.

    Si el médico es Artículo 8 y se selecciona un grupo, las mismas fechas
    se aplican a todos los integrantes de ese grupo. Así el grupo comparte
    un único calendario de guardias y se evita tener que repetir la carga.
    """
    db = SessionLocal()

    try:
        medico = (
            db.query(Medico)
            .filter(Medico.id_medico == id_medico)
            .first()
        )

        if not medico:
            return {"ok": False, "mensaje": "El médico no existe."}

        fechas_limpias = sorted({
            _convertir_fecha(fecha)
            for fecha in (fechas or [])
            if _convertir_fecha(fecha)
        })

        # La inactividad se evalúa individualmente más abajo. Esto es
        # especialmente importante para un grupo Artículo 8: si un
        # integrante está inactivo, los demás integrantes sí pueden
        # conservar el día asignado.
        ids_medicos = [id_medico]

        grupo = None
        if id_grupo_articulo8:
            grupo = (
                db.query(GrupoArticulo8)
                .filter(GrupoArticulo8.id_grupo == int(id_grupo_articulo8))
                .first()
            )

            if not grupo:
                return {"ok": False, "mensaje": "El grupo de Artículo 8 seleccionado no existe."}

            if not _es_elegible_grupo(medico):
                return {
                    "ok": False,
                    "mensaje": "Los grupos solo pueden utilizarse con médicos Artículo 8 o Médicos Internos."
                }

            ids_medicos = [
                fila.id_medico
                for fila in (
                    db.query(GrupoArticulo8Medico)
                    .filter(GrupoArticulo8Medico.id_grupo == grupo.id_grupo)
                    .order_by(GrupoArticulo8Medico.id_medico)
                    .all()
                )
            ]

            if id_medico not in ids_medicos:
                return {
                    "ok": False,
                    "mensaje": "El médico no pertenece al grupo seleccionado."
                }

        # Para un grupo, cada médico conserva únicamente sus fechas válidas
        # según su propia inactividad.
        for medico_id in ids_medicos:
            db.query(Guardia).filter(
                Guardia.id_medico == medico_id
            ).delete(synchronize_session=False)

            medico_destino = (
                db.query(Medico)
                .filter(Medico.id_medico == medico_id)
                .first()
            )

            if not medico_destino:
                continue

            fechas_medico = [
                fecha for fecha in fechas_limpias
                if not _medico_inactivo_en_fecha(medico_destino, fecha)
            ]

            for fecha in fechas_medico:
                db.add(
                    Guardia(
                        id_medico=medico_id,
                        fecha_guardia=fecha,
                        activo=True,
                        id_grupo_articulo8=(
                            grupo.id_grupo if grupo else None
                        )
                    )
                )

        db.commit()

        if grupo:
            mensaje = (
                f"Se guardaron {len(fechas_limpias)} día(s) de guardia "
                f"para el grupo «{grupo.nombre}»."
            )
        else:
            mensaje = (
                f"Se guardaron {len(fechas_limpias)} día(s) de guardia "
                f"para el médico."
            )

        return {
            "ok": True,
            "mensaje": mensaje,
            "cantidad": len(fechas_limpias)
        }

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "mensaje": f"No se pudieron guardar las guardias: {e}"
        }
    finally:
        db.close()


def eliminar_guardia_medico(id_medico, fecha):
    db = SessionLocal()
    try:
        fecha = _convertir_fecha(fecha)
        eliminadas = (
            db.query(Guardia)
            .filter(
                Guardia.id_medico == id_medico,
                Guardia.fecha_guardia == fecha
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return {"ok": True, "cantidad": eliminadas}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"No se pudo eliminar la guardia: {e}"}
    finally:
        db.close()


# ============================================================
# GRUPOS ARTÍCULO 8
# ============================================================

def listar_grupos_articulo8():
    db = SessionLocal()
    try:
        grupos = (
            db.query(GrupoArticulo8)
            .order_by(GrupoArticulo8.nombre.asc())
            .all()
        )

        salida = []
        for grupo in grupos:
            miembros = (
                db.query(GrupoArticulo8Medico)
                .filter(GrupoArticulo8Medico.id_grupo == grupo.id_grupo)
                .count()
            )
            salida.append({
                "id_grupo": grupo.id_grupo,
                "nombre": grupo.nombre,
                "cantidad_medicos": miembros,
            })

        return salida
    finally:
        db.close()


def obtener_grupo_medico(id_medico):
    db = SessionLocal()
    try:
        fila = (
            db.query(GrupoArticulo8Medico, GrupoArticulo8)
            .join(
                GrupoArticulo8,
                GrupoArticulo8.id_grupo == GrupoArticulo8Medico.id_grupo
            )
            .filter(GrupoArticulo8Medico.id_medico == id_medico)
            .first()
        )

        if not fila:
            return None

        relacion, grupo = fila
        return {
            "id_grupo": grupo.id_grupo,
            "nombre": grupo.nombre,
        }
    finally:
        db.close()


def obtener_miembros_grupo_articulo8(id_grupo):
    db = SessionLocal()
    try:
        filas = (
            db.query(Medico)
            .join(
                GrupoArticulo8Medico,
                GrupoArticulo8Medico.id_medico == Medico.id_medico
            )
            .filter(GrupoArticulo8Medico.id_grupo == id_grupo)
            .order_by(Medico.apellidos.asc(), Medico.nombres.asc())
            .all()
        )

        return [
            {
                "id_medico": m.id_medico,
                "nombre": f"{m.nombres or ''} {m.apellidos or ''}".strip(),
                "cedula": m.cedula or "",
            }
            for m in filas
        ]
    finally:
        db.close()


def obtener_mapa_grupos_medicos():
    """
    Devuelve {id_medico: {"id_grupo":, "nombre":}} para todos los médicos
    que actualmente pertenecen a algún grupo Artículo 8. Sirve para que la
    interfaz impida agregar un médico a un segundo grupo.
    """
    db = SessionLocal()
    try:
        filas = (
            db.query(GrupoArticulo8Medico, GrupoArticulo8)
            .join(
                GrupoArticulo8,
                GrupoArticulo8.id_grupo == GrupoArticulo8Medico.id_grupo
            )
            .all()
        )

        return {
            relacion.id_medico: {
                "id_grupo": grupo.id_grupo,
                "nombre": grupo.nombre,
            }
            for relacion, grupo in filas
        }
    finally:
        db.close()


def _medico_en_otro_grupo(db, ids, id_grupo_excluir=None):
    """
    Busca el primer médico de `ids` que ya pertenezca a un grupo distinto
    de `id_grupo_excluir`. Devuelve (medico, grupo) o None.
    """
    consulta = (
        db.query(GrupoArticulo8Medico, Medico, GrupoArticulo8)
        .join(Medico, Medico.id_medico == GrupoArticulo8Medico.id_medico)
        .join(
            GrupoArticulo8,
            GrupoArticulo8.id_grupo == GrupoArticulo8Medico.id_grupo
        )
        .filter(GrupoArticulo8Medico.id_medico.in_(ids))
    )

    if id_grupo_excluir is not None:
        consulta = consulta.filter(
            GrupoArticulo8Medico.id_grupo != id_grupo_excluir
        )

    fila = consulta.first()
    if not fila:
        return None

    _, medico, grupo = fila
    return medico, grupo


def crear_grupo_articulo8(nombre, ids_medicos):
    db = SessionLocal()
    try:
        nombre = (nombre or "").strip().upper()

        if not nombre:
            return {"ok": False, "mensaje": "Indique un nombre para el grupo."}

        ids = sorted({
            int(x) for x in (ids_medicos or [])
            if str(x).isdigit()
        })

        if not ids:
            return {
                "ok": False,
                "mensaje": "Seleccione al menos un médico (Artículo 8 o Interno)."
            }

        existente = (
            db.query(GrupoArticulo8)
            .filter(GrupoArticulo8.nombre == nombre)
            .first()
        )
        if existente:
            return {
                "ok": False,
                "mensaje": "Ya existe un grupo con ese nombre."
            }

        medicos = (
            db.query(Medico)
            .filter(Medico.id_medico.in_(ids))
            .all()
        )

        if len(medicos) != len(ids) or any(not _es_elegible_grupo(m) for m in medicos):
            return {
                "ok": False,
                "mensaje": "Un grupo médico solo puede contener médicos Artículo 8 o Médicos Internos."
            }

        conflicto = _medico_en_otro_grupo(db, ids)
        if conflicto:
            medico, grupo = conflicto
            nombre_medico = f"{medico.nombres or ''} {medico.apellidos or ''}".strip()
            return {
                "ok": False,
                "mensaje": (
                    f"El Dr(a). {nombre_medico} ya pertenece al grupo "
                    f"«{grupo.nombre}». Un médico Artículo 8 solo puede "
                    f"estar en un grupo a la vez."
                )
            }

        ahora = datetime.now()
        grupo = GrupoArticulo8(
            nombre=nombre,
            fecha_registro=ahora,
            fecha_actualizacion=ahora
        )
        db.add(grupo)
        db.flush()

        for id_medico in ids:
            db.add(
                GrupoArticulo8Medico(
                    id_grupo=grupo.id_grupo,
                    id_medico=id_medico
                )
            )

        db.commit()

        return {
            "ok": True,
            "mensaje": f"Grupo «{nombre}» creado correctamente.",
            "id_grupo": grupo.id_grupo
        }

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "mensaje": f"No se pudo crear el grupo: {e}"
        }
    finally:
        db.close()


def actualizar_miembros_grupo_articulo8(id_grupo, ids_medicos):
    db = SessionLocal()
    try:
        grupo = (
            db.query(GrupoArticulo8)
            .filter(GrupoArticulo8.id_grupo == id_grupo)
            .first()
        )
        if not grupo:
            return {"ok": False, "mensaje": "El grupo no existe."}

        ids = sorted({
            int(x) for x in (ids_medicos or [])
            if str(x).isdigit()
        })
        if not ids:
            return {
                "ok": False,
                "mensaje": "Seleccione al menos un médico (Artículo 8 o Interno)."
            }

        medicos = db.query(Medico).filter(Medico.id_medico.in_(ids)).all()
        if len(medicos) != len(ids) or any(not _es_elegible_grupo(m) for m in medicos):
            return {
                "ok": False,
                "mensaje": "El grupo solo puede contener médicos Artículo 8 o Médicos Internos."
            }

        conflicto = _medico_en_otro_grupo(db, ids, id_grupo_excluir=id_grupo)
        if conflicto:
            medico, otro_grupo = conflicto
            nombre_medico = f"{medico.nombres or ''} {medico.apellidos or ''}".strip()
            return {
                "ok": False,
                "mensaje": (
                    f"El Dr(a). {nombre_medico} ya pertenece al grupo "
                    f"«{otro_grupo.nombre}». Un médico Artículo 8 solo puede "
                    f"estar en un grupo a la vez."
                )
            }

        # Miembros actuales antes del cambio
        miembros_actuales = {
            fila.id_medico
            for fila in (
                db.query(GrupoArticulo8Medico)
                .filter(GrupoArticulo8Medico.id_grupo == id_grupo)
                .all()
            )
        }
        nuevos = set(ids)
        removidos = miembros_actuales - nuevos

        # Quienes salen del grupo: borrar sus guardias de ese grupo
        if removidos:
            db.query(Guardia).filter(
                Guardia.id_medico.in_(removidos),
                Guardia.id_grupo_articulo8 == id_grupo
            ).delete(synchronize_session=False)

        db.query(GrupoArticulo8Medico).filter(
            GrupoArticulo8Medico.id_grupo == id_grupo
        ).delete(synchronize_session=False)

        for id_medico in ids:
            db.add(
                GrupoArticulo8Medico(
                    id_grupo=id_grupo,
                    id_medico=id_medico
                )
            )

        grupo.fecha_actualizacion = datetime.now()
        db.commit()

        return {"ok": True, "mensaje": "Integrantes del grupo actualizados."}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"No se pudo actualizar el grupo: {e}"}
    finally:
        db.close()


# ============================================================
# HORARIO DEL GRUPO ARTÍCULO 8
# ============================================================
# El horario pertenece al grupo, no a un médico en particular: al
# guardarlo se aplican las mismas fechas a todos los integrantes.

def obtener_horario_grupo_articulo8(id_grupo):
    db = SessionLocal()
    try:
        fechas = (
            db.query(Guardia.fecha_guardia)
            .filter(
                Guardia.id_grupo_articulo8 == id_grupo,
                Guardia.activo == True
            )
            .distinct()
            .all()
        )

        return sorted({
            _convertir_fecha(fecha[0])
            for fecha in fechas
            if _convertir_fecha(fecha[0])
        })
    finally:
        db.close()


def guardar_horario_grupo_articulo8(id_grupo, fechas):
    """
    Reemplaza el horario de guardias del grupo. Las mismas fechas se
    aplican a todos los integrantes; cada uno conserva únicamente las
    fechas en las que no está inactivo.
    """
    db = SessionLocal()
    try:
        grupo = (
            db.query(GrupoArticulo8)
            .filter(GrupoArticulo8.id_grupo == id_grupo)
            .first()
        )
        if not grupo:
            return {"ok": False, "mensaje": "El grupo no existe."}

        ids_medicos = [
            fila.id_medico
            for fila in (
                db.query(GrupoArticulo8Medico)
                .filter(GrupoArticulo8Medico.id_grupo == id_grupo)
                .order_by(GrupoArticulo8Medico.id_medico)
                .all()
            )
        ]

        if not ids_medicos:
            return {
                "ok": False,
                "mensaje": "El grupo no tiene integrantes registrados."
            }

        fechas_limpias = sorted({
            _convertir_fecha(fecha)
            for fecha in (fechas or [])
            if _convertir_fecha(fecha)
        })

        for medico_id in ids_medicos:
            db.query(Guardia).filter(
                Guardia.id_medico == medico_id
            ).delete(synchronize_session=False)

            medico_destino = (
                db.query(Medico)
                .filter(Medico.id_medico == medico_id)
                .first()
            )
            if not medico_destino:
                continue

            fechas_medico = [
                fecha for fecha in fechas_limpias
                if not _medico_inactivo_en_fecha(medico_destino, fecha)
            ]

            for fecha in fechas_medico:
                db.add(
                    Guardia(
                        id_medico=medico_id,
                        fecha_guardia=fecha,
                        activo=True,
                        id_grupo_articulo8=grupo.id_grupo
                    )
                )

        grupo.fecha_actualizacion = datetime.now()
        db.commit()

        return {
            "ok": True,
            "mensaje": (
                f"Se guardó el horario del grupo «{grupo.nombre}» "
                f"({len(fechas_limpias)} día(s))."
            ),
            "cantidad": len(fechas_limpias)
        }

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "mensaje": f"No se pudo guardar el horario del grupo: {e}"
        }
    finally:
        db.close()
        
def eliminar_grupo_articulo8(id_grupo):
    """
    Elimina el grupo. Los médicos que pertenecían a él quedan
    sin grupo (se borran solo las relaciones, no los médicos).
    Las guardias que tenían id_grupo_articulo8 se desvinculan
    (se pone NULL) para no perder el historial.
    """
    db = SessionLocal()
    try:
        grupo = (
            db.query(GrupoArticulo8)
            .filter(GrupoArticulo8.id_grupo == id_grupo)
            .first()
        )
        if not grupo:
            return {"ok": False, "mensaje": "El grupo no existe."}

        nombre = grupo.nombre

        # Los médicos quedan sin grupo
        db.query(GrupoArticulo8Medico).filter(
            GrupoArticulo8Medico.id_grupo == id_grupo
        ).delete(synchronize_session=False)

        # Desvincular guardias del grupo (no se borran las fechas)
        db.query(Guardia).filter(
            Guardia.id_grupo_articulo8 == id_grupo
        )
                # Borrar guardias del grupo (los médicos quedan en cero)
        db.query(Guardia).filter(
            Guardia.id_grupo_articulo8 == id_grupo
        ).delete(synchronize_session=False)

        db.delete(grupo)
        db.commit()

        return {
            "ok": True,
            "mensaje": f"Grupo «{nombre}» eliminado. Los médicos quedaron sin grupo."
        }

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "mensaje": f"No se pudo eliminar el grupo: {e}"
        }
    finally:
        db.close()


# ============================================================
# CALENDARIO GENERAL
# ============================================================

def obtener_guardias_mes(
    anio,
    mes,
    texto_busqueda="",
    cargo="Todos los cargos",
    centro="Todos los centros",
    especialidad="Todas las especialidades"
):
    """
    Devuelve las guardias manuales de un mes.

    `cargo` puede ser un texto o una lista de hasta varios cargos.
    Esto permite mostrar simultáneamente, por ejemplo, ARTICULO 8
    y MEDICO INTERNO.
    """
    db = SessionLocal()

    try:
        fecha_inicio_mes = date(anio, mes, 1)
        if mes == 12:
            fecha_fin_mes = date(anio + 1, 1, 1)
        else:
            fecha_fin_mes = date(anio, mes + 1, 1)

        texto_busqueda = (texto_busqueda or "").strip().lower()
        cargos = _cargos_normalizados(cargo)
        centro_filtro = _normalizar_texto(centro)
        especialidad_filtro = _normalizar_texto(especialidad)

        registros = (
            db.query(Guardia, Medico)
            .join(Medico, Guardia.id_medico == Medico.id_medico)
            .filter(
                Guardia.activo == True,
                Guardia.fecha_guardia >= fecha_inicio_mes,
                Guardia.fecha_guardia < fecha_fin_mes
            )
            .all()
        )

        guardias_por_dia = {}
        medicos_inactivos_mes = {}

        for guardia, medico in registros:
            fecha_guardia = _convertir_fecha(guardia.fecha_guardia)
            if not fecha_guardia:
                continue

            nombre = f"{medico.nombres or ''} {medico.apellidos or ''}".strip()
            cargo_medico = (medico.cargo or "").strip()
            centro_medico = (medico.centro_salud or "").strip()
            especialidad_medico = (medico.especialidad or "").strip()

            if texto_busqueda:
                texto_completo = " ".join([
                    nombre,
                    medico.cedula or "",
                    medico.codigo or ""
                ]).lower()
                if texto_busqueda not in texto_completo:
                    continue

            if cargos and _normalizar_texto(cargo_medico) not in cargos:
                continue

            if (
                centro_filtro
                and centro_filtro != "todos los centros"
                and _normalizar_texto(centro_medico) != centro_filtro
            ):
                continue

            if (
                especialidad_filtro
                and especialidad_filtro != "todas las especialidades"
                and _normalizar_texto(especialidad_medico) != especialidad_filtro
            ):
                continue

            if (
                medico.id_medico not in medicos_inactivos_mes
                and _tiene_inactividad_configurada(medico)
            ):
                inicio_inactividad = _convertir_fecha(medico.fecha_inicio_inactividad)
                fin_inactividad = _convertir_fecha(medico.fecha_fin_inactividad)
                causa = (medico.causa_inactividad or "").strip() or "Reposo médico"
                definitiva = _causa_es_definitiva(causa)

                if _inactividad_se_solapa_con_mes(
                    inicio_inactividad,
                    fin_inactividad,
                    fecha_inicio_mes,
                    fecha_fin_mes - timedelta(days=1),
                    es_definitiva=definitiva
                ):
                    medicos_inactivos_mes[medico.id_medico] = {
                        "id_medico": medico.id_medico,
                        "nombre": nombre,
                        "especialidad": especialidad_medico,
                        "causa": causa,
                        "fecha_inicio_inactividad": inicio_inactividad,
                        "fecha_fin_inactividad": fin_inactividad,
                        "es_definitiva": definitiva,
                    }

            esta_inactivo = _medico_inactivo_en_fecha(medico, fecha_guardia)

            # Las guardias dentro de una inactividad no se muestran en
            # el calendario general, salvo cuando el usuario busca al médico.
            if esta_inactivo and not texto_busqueda:
                continue

            guardias_por_dia.setdefault(fecha_guardia, []).append({
                "id_medico": medico.id_medico,
                "nombre": nombre,
                "nombres": (medico.nombres or "").strip(),
                "apellidos": (medico.apellidos or "").strip(),
                "cedula": medico.cedula or "",
                "codigo": medico.codigo or "",
                "cargo": cargo_medico,
                "centro": centro_medico,
                "especialidad": especialidad_medico,
                "telefono": medico.telefono or "",
                "inactivo": esta_inactivo,
                "causa_inactividad": (medico.causa_inactividad or "").strip(),
                "id_grupo_articulo8": guardia.id_grupo_articulo8,
            })

        # Detectar cobertura Artículo 8 vs. Internos usando TODOS los cargos,
        # independientemente de los filtros visuales.
        cobertura = {}
        for fecha, medicos in list(guardias_por_dia.items()):
            if not isinstance(fecha, date):
                continue
            tiene_art8 = any(_normalizar_texto(m.get("cargo")) == "articulo 8" for m in medicos)
            tiene_interno = any("intern" in _normalizar_texto(m.get("cargo")) for m in medicos)
            cobertura[fecha] = {
                "tiene_articulo8": tiene_art8,
                "tiene_interno": tiene_interno,
                "falta_interno": tiene_art8 and not tiene_interno,
            }

        # Cuando el filtro oculta uno de los cargos, recalculamos cobertura
        # directamente en BD para que la alerta siga siendo correcta.
        fechas_con_art8 = {
            _convertir_fecha(g.fecha_guardia)
            for g, m in registros
            if _convertir_fecha(g.fecha_guardia)
            and _normalizar_texto(m.cargo) == "articulo 8"
            and not _medico_inactivo_en_fecha(m, _convertir_fecha(g.fecha_guardia))
        }
        fechas_con_interno = {
            _convertir_fecha(g.fecha_guardia)
            for g, m in registros
            if _convertir_fecha(g.fecha_guardia)
            and "intern" in _normalizar_texto(m.cargo)
            and not _medico_inactivo_en_fecha(m, _convertir_fecha(g.fecha_guardia))
        }

        for fecha in fechas_con_art8 | fechas_con_interno:
            cobertura[fecha] = {
                "tiene_articulo8": fecha in fechas_con_art8,
                "tiene_interno": fecha in fechas_con_interno,
                "falta_interno": fecha in fechas_con_art8 and fecha not in fechas_con_interno,
            }

        guardias_por_dia["__cobertura__"] = cobertura
        guardias_por_dia["__medicos_inactivos_mes__"] = list(
            medicos_inactivos_mes.values()
        )

        for fecha, medicos in guardias_por_dia.items():
            if isinstance(fecha, date):
                medicos.sort(key=lambda m: (m.get("nombre") or "").lower())

        return guardias_por_dia

    finally:
        db.close()


def obtener_resumen_guardias_hoy():
    hoy = date.today()

    try:
        guardias_mes = obtener_guardias_mes(
            hoy.year,
            hoy.month,
            cargo="Todos los cargos",
            centro="Todos los centros",
            especialidad="Todas las especialidades"
        )

        medicos_hoy = guardias_mes.get(hoy, [])

        # Solo médicos que realmente están activos para ese día
        activos = [
            medico
            for medico in medicos_hoy
            if not medico.get("inactivo")
        ]

        # ----------------------------------------------------
        # NOMBRES
        # ----------------------------------------------------

        nombres = []

        for medico in activos:

            nombre = (
                medico.get("nombre")
                or f"{medico.get('nombres', '')} "
                   f"{medico.get('apellidos', '')}"
            ).strip()

            if nombre:
                nombres.append(nombre)

        # ----------------------------------------------------
        # ESPECIALIDADES
        # ----------------------------------------------------

        especialidades = set()

        for medico in activos:

            especialidad = (
                medico.get("especialidad") or ""
            ).strip()

            if especialidad:
                especialidades.add(
                    _normalizar_texto(especialidad)
                )

        return {
            "cantidad": len(activos),
            "especialidades": len(especialidades),
            "nombres": nombres,
            "medicos": activos
        }

    except Exception as error:

        print(
            f"[ResumenGuardias] Error: {error}"
        )

        return {
            "cantidad": 0,
            "especialidades": 0,
            "nombres": [],
            "medicos": []
        }
