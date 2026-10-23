from datetime import datetime, date

from database import SessionLocal
from models.oficio import Oficio


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


def _convertir_fecha(valor):

    if valor is None:
        return None

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):

        valor = valor.strip()

        for formato in ("%Y-%m-%d", "%d/%m/%Y"):

            try:
                return datetime.strptime(valor, formato).date()

            except ValueError:
                continue

        return None

    return None


# ============================================================
# SIGUIENTE NÚMERO DE OFICIO (correlativo sugerido)
# ============================================================

def obtener_siguiente_numero():
    """
    Sugiere el próximo número de oficio del año actual.
    Cuando cambia el año, vuelve a empezar en 001.
    """

    db = SessionLocal()

    try:
        anio_actual = date.today().year

        # Solo oficios del año actual
        oficios = db.query(Oficio.numero).filter(
            Oficio.fecha >= date(anio_actual, 1, 1),
            Oficio.fecha <= date(anio_actual, 12, 31)
        ).all()

        mayor = 0

        for (numero,) in oficios:
            numero_limpio = "".join(
                caracter
                for caracter in (numero or "")
                if caracter.isdigit()
            )

            if numero_limpio.isdigit():
                mayor = max(mayor, int(numero_limpio))

        return str(mayor + 1).zfill(3)

    finally:
        db.close()


# ============================================================
# LISTAR OFICIOS
# ============================================================

def listar_oficios(texto_busqueda=""):
    """
    Devuelve todos los oficios, del más reciente al más antiguo.
    Si se pasa texto_busqueda, filtra por número, destinatario,
    asunto u observación.
    """

    db = SessionLocal()

    try:

        query = db.query(Oficio)

        texto_busqueda = (texto_busqueda or "").strip().lower()

        oficios = query.order_by(
            Oficio.fecha.desc(),
            Oficio.id_oficio.desc()
        ).all()

        resultado = []

        for oficio in oficios:

            if texto_busqueda:

                texto_completo = " ".join([
                    oficio.numero or "",
                    oficio.destinatario or "",
                    oficio.asunto or "",
                    oficio.observacion or ""
                ]).lower()

                if texto_busqueda not in texto_completo:
                    continue

            resultado.append({
                "id_oficio": oficio.id_oficio,
                "numero": oficio.numero,
                "fecha": oficio.fecha,
                "destinatario": oficio.destinatario,
                "asunto": oficio.asunto,
                "observacion": oficio.observacion or ""
            })

        return resultado

    finally:
        db.close()


# ============================================================
# OBTENER UN OFICIO
# ============================================================

def obtener_oficio(id_oficio):

    db = SessionLocal()

    try:

        return db.query(Oficio).filter(
            Oficio.id_oficio == id_oficio
        ).first()

    finally:
        db.close()


# ============================================================
# VALIDAR NÚMERO DUPLICADO
# ============================================================

def numero_ya_existe(numero, id_oficio_excluir=None, anio=None):
    """
    Verifica si el número ya existe en el mismo año.
    Si no se pasa 'anio', usa el año actual.
    """

    db = SessionLocal()

    try:
        if anio is None:
            anio = date.today().year

        query = db.query(Oficio).filter(
            Oficio.numero == numero,
            Oficio.fecha >= date(anio, 1, 1),
            Oficio.fecha <= date(anio, 12, 31)
        )

        if id_oficio_excluir:
            query = query.filter(
                Oficio.id_oficio != id_oficio_excluir
            )

        return db.query(query.exists()).scalar()

    finally:
        db.close()


# ============================================================
# CREAR OFICIO
# ============================================================

def crear_oficio(datos):
    """
    datos: dict con las llaves
        numero, fecha, destinatario, asunto, observacion
    """

    db = SessionLocal()

    try:

        oficio = Oficio(
            numero=_valor_o_none(datos.get("numero")),
            fecha=_convertir_fecha(datos.get("fecha")),
            destinatario=_valor_o_none(datos.get("destinatario")),
            asunto=_valor_o_none(datos.get("asunto")),
            observacion=_valor_o_none(datos.get("observacion"))
        )

        db.add(oficio)
        db.commit()
        db.refresh(oficio)

        return oficio.id_oficio

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# ACTUALIZAR OFICIO
# ============================================================

def actualizar_oficio(id_oficio, datos):

    db = SessionLocal()

    try:

        oficio = db.query(Oficio).filter(
            Oficio.id_oficio == id_oficio
        ).first()

        if not oficio:
            return False

        oficio.numero = _valor_o_none(datos.get("numero"))
        oficio.fecha = _convertir_fecha(datos.get("fecha"))
        oficio.destinatario = _valor_o_none(datos.get("destinatario"))
        oficio.asunto = _valor_o_none(datos.get("asunto"))
        oficio.observacion = _valor_o_none(datos.get("observacion"))

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# ELIMINAR OFICIO
# ============================================================

def eliminar_oficio(id_oficio):

    db = SessionLocal()

    try:

        oficio = db.query(Oficio).filter(
            Oficio.id_oficio == id_oficio
        ).first()

        if not oficio:
            return False

        db.delete(oficio)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# RESUMEN PARA EL PANEL DE INICIO
# ============================================================

def obtener_resumen_oficios():
    """
    Devuelve el total de oficios registrados y los datos del
    último oficio (el más reciente), para mostrarlo como tarjeta
    de resumen en la pantalla de Inicio.
    """

    try:

        oficios = listar_oficios()

        ultimo = oficios[0] if oficios else None

        return {
            "total": len(oficios),
            "ultimo_numero": ultimo["numero"] if ultimo else "-",
            "ultimo_destinatario": (
                ultimo["destinatario"] if ultimo else ""
            ),
            "ultimo_asunto": ultimo["asunto"] if ultimo else "",
            "ultimo_fecha": ultimo["fecha"] if ultimo else None
        }

    except Exception as error:

        print(
            f"[ResumenOficios] Error: {error}"
        )

        return {
            "total": 0,
            "ultimo_numero": "-",
            "ultimo_destinatario": "",
            "ultimo_asunto": "",
            "ultimo_fecha": None
        }
