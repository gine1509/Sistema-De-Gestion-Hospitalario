from datetime import datetime, date, timedelta
from sqlalchemy import text
from database import SessionLocal
from models.personal_direccion import PersonalDireccion, HorarioDireccion


DIAS_SEMANA = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
    7: "Domingo",
}

# El horario del personal de dirección solo se asigna de lunes a viernes.
DIAS_LABORALES_DIRECCION = (1, 2, 3, 4, 5)


def _none(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


def listar_personal_direccion(texto=""):
    db = SessionLocal()
    try:
        query = db.query(PersonalDireccion)
        texto = (texto or "").strip()
        if texto:
            patron = f"%{texto}%"
            query = query.filter(
                (PersonalDireccion.nombres.ilike(patron)) |
                (PersonalDireccion.apellidos.ilike(patron)) |
                (PersonalDireccion.cedula.ilike(patron)) |
                (PersonalDireccion.cargo.ilike(patron))
            )
        personas = query.order_by(PersonalDireccion.id_personal.desc()).all()
        resultado = []
        for p in personas:
            horarios = (
                db.query(HorarioDireccion)
                .filter(
                    HorarioDireccion.id_personal == p.id_personal,
                    HorarioDireccion.activo == True
                )
                .order_by(HorarioDireccion.dia_semana)
                .all()
            )
            resultado.append({
                "id_personal": p.id_personal,
                "cedula": p.cedula or "",
                "nombres": p.nombres or "",
                "apellidos": p.apellidos or "",
                "nombre": f"{p.nombres or ''} {p.apellidos or ''}".strip(),
                "telefono": p.telefono or "",
                "correo": p.correo or "",
                "cargo": p.cargo or "",
                "fecha_ingreso": p.fecha_ingreso,
                "activo": bool(p.activo),
                "observacion": p.observacion or "",
                "causa_inactividad": p.causa_inactividad or "",
                "fecha_inicio_inactividad": p.fecha_inicio_inactividad,
                "fecha_fin_inactividad": p.fecha_fin_inactividad,
                "tiempo_inactividad": p.tiempo_inactividad or "",
                "horarios": [
                    {
                        "dia": h.dia_semana,
                        "dia_nombre": DIAS_SEMANA.get(h.dia_semana, ""),
                        "entrada": h.hora_entrada,
                        "salida": h.hora_salida,
                    }
                    for h in horarios
                ],
            })
        return resultado
    finally:
        db.close()


def obtener_personal_direccion(id_personal):
    personas = listar_personal_direccion()
    return next((p for p in personas if p["id_personal"] == id_personal), None)




def crear_personal_direccion(datos):
    db = SessionLocal()
    try:
        cedula = _none(datos.get("cedula"))
        if not cedula:
            return {"ok": False, "mensaje": "La cédula es obligatoria."}
        if db.query(PersonalDireccion).filter(PersonalDireccion.cedula == cedula).first():
            return {"ok": False, "mensaje": "Ya existe personal registrado con esa cédula."}

        persona = PersonalDireccion(
            cedula=cedula,
            nombres=(datos.get("nombres") or "").strip().upper(),
            apellidos=(datos.get("apellidos") or "").strip().upper(),
            telefono=_none(datos.get("telefono")),
            correo=_none(datos.get("correo")),
            cargo=_none(datos.get("cargo")),
            fecha_ingreso=datos.get("fecha_ingreso"),
            activo=bool(datos.get("activo", True)),
            observacion=_none(datos.get("observacion")),
            causa_inactividad=_none(datos.get("causa_inactividad")),
            fecha_inicio_inactividad=datos.get("fecha_inicio_inactividad"),
            fecha_fin_inactividad=datos.get("fecha_fin_inactividad"),
            tiempo_inactividad=_none(datos.get("tiempo_inactividad")),
            fecha_registro=datetime.now(),
            fecha_actualizacion=datetime.now(),
        )
        if not persona.nombres or not persona.apellidos:
            return {"ok": False, "mensaje": "Nombres y apellidos son obligatorios."}
        db.add(persona)
        db.commit()
        db.refresh(persona)
        return {"ok": True, "mensaje": "Personal de dirección registrado correctamente.", "id_personal": persona.id_personal}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al registrar: {e}"}
    finally:
        db.close()
        
def buscar_por_cedula(cedula):
    db = SessionLocal()
    try:
        persona = (
            db.query(PersonalDireccion)
            .filter(PersonalDireccion.cedula == cedula)
            .first()
        )
        if not persona:
            return None

        return {
            "id_personal": persona.id_personal,
            "cedula": persona.cedula or "",
            "nombres": persona.nombres or "",
            "apellidos": persona.apellidos or "",
            "telefono": persona.telefono or "",
            "correo": persona.correo or "",
            "cargo": persona.cargo or "",
            "fecha_ingreso": persona.fecha_ingreso,
            "activo": bool(persona.activo),
            "observacion": persona.observacion or "",
            "causa_inactividad": persona.causa_inactividad or "",
            "fecha_inicio_inactividad": persona.fecha_inicio_inactividad,
            "fecha_fin_inactividad": persona.fecha_fin_inactividad,
            "tiempo_inactividad": persona.tiempo_inactividad or "",
        }
    finally:
        db.close()


def actualizar_personal_direccion(id_personal, datos):
    db = SessionLocal()
    try:
        persona = db.query(PersonalDireccion).filter(PersonalDireccion.id_personal == id_personal).first()
        if not persona:
            return {"ok": False, "mensaje": "El registro no existe."}

        cedula = _none(datos.get("cedula"))
        existente = db.query(PersonalDireccion).filter(
            PersonalDireccion.cedula == cedula,
            PersonalDireccion.id_personal != id_personal
        ).first()
        if existente:
            return {"ok": False, "mensaje": "Ya existe otra persona con esa cédula."}

        persona.cedula = cedula
        persona.nombres = (datos.get("nombres") or "").strip().upper()
        persona.apellidos = (datos.get("apellidos") or "").strip().upper()
        persona.telefono = _none(datos.get("telefono"))
        persona.correo = _none(datos.get("correo"))
        persona.cargo = _none(datos.get("cargo"))
        persona.fecha_ingreso = datos.get("fecha_ingreso")
        persona.activo = bool(datos.get("activo", True))
        persona.observacion = _none(datos.get("observacion"))
        persona.causa_inactividad = _none(datos.get("causa_inactividad"))
        persona.fecha_inicio_inactividad = datos.get("fecha_inicio_inactividad")
        persona.fecha_fin_inactividad = datos.get("fecha_fin_inactividad")
        persona.tiempo_inactividad = _none(datos.get("tiempo_inactividad"))
        persona.fecha_actualizacion = datetime.now()

        db.commit()
        return {"ok": True, "mensaje": "Información actualizada correctamente."}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al actualizar: {e}"}
    finally:
        db.close()


def eliminar_personal_direccion(id_personal):
    db = SessionLocal()
    try:
        persona = db.query(PersonalDireccion).filter(PersonalDireccion.id_personal == id_personal).first()
        if not persona:
            return {"ok": False, "mensaje": "El registro no existe."}
        db.query(HorarioDireccion).filter(HorarioDireccion.id_personal == id_personal).delete()
        db.delete(persona)
        db.commit()
        return {"ok": True, "mensaje": "Registro eliminado correctamente."}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al eliminar: {e}"}
    finally:
        db.close()


def guardar_horario_direccion(id_personal, dias):
    """
    Asigna el horario (solo los días, sin hora de entrada/salida) al
    personal de dirección. `dias` es una lista de números de día
    (1=Lunes ... 5=Viernes).
    """
    db = SessionLocal()
    try:
        if not db.query(PersonalDireccion).filter(PersonalDireccion.id_personal == id_personal).first():
            return {"ok": False, "mensaje": "El personal seleccionado no existe."}

        db.query(HorarioDireccion).filter(HorarioDireccion.id_personal == id_personal).delete()

        for dia in dias:
            dia = int(dia)
            if dia not in DIAS_LABORALES_DIRECCION:
                continue
            db.add(HorarioDireccion(
                id_personal=id_personal,
                dia_semana=dia,
                hora_entrada="-",
                hora_salida="-",
                activo=True
            ))

        db.commit()
        return {"ok": True, "mensaje": "Horario asignado correctamente."}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al guardar horario: {e}"}
    finally:
        db.close()


def _a_fecha(valor):
    """Normaliza un valor de fecha (date/datetime) a `date`, o None."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return None


def obtener_calendario_horario_direccion(anio, mes, texto_busqueda=""):
    """
    Calcula, para cada día del mes indicado, qué personal de dirección
    tiene horario asignado según el día de la semana que le corresponde.

    Reglas aplicadas por persona (igual que en médicos):

    - El horario solo se muestra a partir de su fecha de ingreso. Si no
      tiene fecha de ingreso registrada, se muestra sin límite inferior.
    - Si está inactivo y tiene fecha de inicio y fin de inactividad, el
      horario se oculta únicamente dentro de ese rango (se ve antes del
      inicio y después del fin).
    - Si está inactivo y solo tiene fecha de inicio (sin fin), el horario
      se muestra hasta antes de esa fecha; como no hay fin, deja de
      mostrarse desde ahí en adelante hasta que se reactive o se le
      coloque una fecha de fin.
    - Si está inactivo sin ninguna fecha registrada, no se muestra.

    Retorna un diccionario:

        {
            date(2026, 9, 1): [
                {"id_personal": 1, "nombre": "JUAN PÉREZ", "cargo": "..."}
            ],
            ...
        }
    """
    db = SessionLocal()
    try:
        fecha_inicio_mes = date(anio, mes, 1)
        if mes == 12:
            fecha_fin_mes = date(anio + 1, 1, 1) - timedelta(days=1)
        else:
            fecha_fin_mes = date(anio, mes + 1, 1) - timedelta(days=1)

        query = db.query(PersonalDireccion)

        texto = (texto_busqueda or "").strip()
        if texto:
            patron = f"%{texto}%"
            query = query.filter(
                (PersonalDireccion.nombres.ilike(patron)) |
                (PersonalDireccion.apellidos.ilike(patron)) |
                (PersonalDireccion.cedula.ilike(patron)) |
                (PersonalDireccion.cargo.ilike(patron))
            )

        personas = query.all()

        dias_por_persona = {}
        for p in personas:
            filas = (
                db.query(HorarioDireccion.dia_semana)
                .filter(
                    HorarioDireccion.id_personal == p.id_personal,
                    HorarioDireccion.activo == True
                )
                .all()
            )
            dias_por_persona[p.id_personal] = {f[0] for f in filas}

        resultado = {}
        dia_actual = fecha_inicio_mes
        while dia_actual <= fecha_fin_mes:
            dia_semana_iso = dia_actual.isoweekday()  # 1=Lunes ... 7=Domingo
            asignados = []
            for p in personas:
                if dia_semana_iso not in dias_por_persona.get(p.id_personal, set()):
                    continue

                # Solo se muestra a partir de la fecha de ingreso.
                # Sin fecha de ingreso registrada, no hay límite inferior.
                fecha_ingreso = _a_fecha(p.fecha_ingreso)
                if fecha_ingreso and dia_actual < fecha_ingreso:
                    continue

                # Se respeta la inactividad con la misma lógica que médicos.
                if not p.activo:
                    inactivo_inicio = _a_fecha(p.fecha_inicio_inactividad)
                    inactivo_fin = _a_fecha(p.fecha_fin_inactividad)

                    if inactivo_inicio and inactivo_fin:
                        if inactivo_inicio <= dia_actual <= inactivo_fin:
                            continue
                    elif inactivo_inicio and not inactivo_fin:
                        if dia_actual >= inactivo_inicio:
                            continue
                    else:
                        # Inactivo sin fechas registradas: no se muestra.
                        continue

                asignados.append({
                    "id_personal": p.id_personal,
                    "nombre": f"{p.nombres or ''} {p.apellidos or ''}".strip(),
                    "cargo": p.cargo or "",
                })
            resultado[dia_actual] = asignados
            dia_actual += timedelta(days=1)

        return resultado
    finally:
        db.close()


# ============================================================
# RESUMEN PARA EL PANEL DE INICIO
# ============================================================

def obtener_resumen_direccion_hoy():
    """
    Devuelve el total de personal de dirección activo y quiénes
    tienen horario asignado el día de hoy, para mostrarlo como
    tarjeta de resumen en la pantalla de Inicio.
    """

    hoy = date.today()

    try:

        personas = listar_personal_direccion()

        total_activo = sum(
            1
            for persona in personas
            if persona["activo"]
        )

        calendario = obtener_calendario_horario_direccion(
            hoy.year,
            hoy.month
        )

        asignados_hoy = calendario.get(hoy, [])

        return {
            "total_activo": total_activo,
            "cantidad_hoy": len(asignados_hoy),
            "nombres_hoy": [
                persona["nombre"]
                for persona in asignados_hoy
            ],
            "es_fin_de_semana": (
                hoy.isoweekday() not in DIAS_LABORALES_DIRECCION
            )
        }

    except Exception as error:

        print(
            f"[ResumenDireccion] Error: {error}"
        )

        return {
            "total_activo": 0,
            "cantidad_hoy": 0,
            "nombres_hoy": [],
            "es_fin_de_semana": False
        }
