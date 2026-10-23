import hashlib
from datetime import datetime

from database import SessionLocal
from models.usuarios import Usuario

# =====================================================
# DATOS DEL USUARIO ADMINISTRADOR INICIAL
# =====================================================
# El sistema no cuenta con registro público de usuarios.
# Este es el único usuario que existe "de fábrica"; el resto
# (rol secretaria) los crea el administrador desde el módulo
# de Configuración.
CEDULA_ADMIN_INICIAL = "V-12345678"
USUARIO_ADMIN_INICIAL = "admin"
CONTRASENA_ADMIN_INICIAL = "1234"

LONGITUD_MINIMA_CONTRASENA = 4


def _none(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


def _hash_contrasena(contrasena):
    """Hash simple pero no reversible para no guardar contraseñas en texto plano."""
    return hashlib.sha256((contrasena or "").encode("utf-8")).hexdigest()


def _verificar_contrasena(contrasena, contrasena_hash):
    return _hash_contrasena(contrasena) == (contrasena_hash or "")


def _a_dict(u):
    return {
        "id_usuario": u.id_usuario,
        "cedula": u.cedula or "",
        "usuario": u.usuario or "",
        "rol": u.rol or "secretaria",
        "activo": bool(u.activo),
        "fecha_registro": u.fecha_registro,
        "fecha_actualizacion": u.fecha_actualizacion,
    }


# =====================================================
# SIEMBRA DEL USUARIO ADMIN INICIAL
# =====================================================

def asegurar_usuario_admin():
    """
    Garantiza que exista el usuario administrador inicial.
    Se puede llamar de forma segura cada vez que arranca la app.
    """
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.rol == "admin").first()
        if existe:
            return

        admin = Usuario(
            cedula=CEDULA_ADMIN_INICIAL,
            usuario=USUARIO_ADMIN_INICIAL,
            contrasena_hash=_hash_contrasena(CONTRASENA_ADMIN_INICIAL),
            rol="admin",
            activo=True,
            fecha_registro=datetime.now(),
            fecha_actualizacion=datetime.now(),
        )
        db.add(admin)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[usuario_service] No se pudo crear el usuario admin inicial: {e}")
    finally:
        db.close()


# =====================================================
# CONSULTAS
# =====================================================

def listar_usuarios(texto="", rol=None):
    db = SessionLocal()
    try:
        query = db.query(Usuario)
        if rol:
            query = query.filter(Usuario.rol == rol)

        texto = (texto or "").strip()
        if texto:
            patron = f"%{texto}%"
            query = query.filter(
                (Usuario.usuario.ilike(patron)) |
                (Usuario.cedula.ilike(patron))
            )

        usuarios = query.order_by(Usuario.id_usuario.desc()).all()
        return [_a_dict(u) for u in usuarios]
    finally:
        db.close()


def obtener_usuario(id_usuario):
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        return _a_dict(u) if u else None
    finally:
        db.close()


def buscar_por_usuario(usuario, excluir_id=None):
    db = SessionLocal()
    try:
        query = db.query(Usuario).filter(Usuario.usuario == usuario)
        if excluir_id:
            query = query.filter(Usuario.id_usuario != excluir_id)
        u = query.first()
        return _a_dict(u) if u else None
    finally:
        db.close()


def buscar_por_cedula(cedula, excluir_id=None):
    db = SessionLocal()
    try:
        query = db.query(Usuario).filter(Usuario.cedula == cedula)
        if excluir_id:
            query = query.filter(Usuario.id_usuario != excluir_id)
        u = query.first()
        return _a_dict(u) if u else None
    finally:
        db.close()


# =====================================================
# AUTENTICACIÓN (LOGIN)
# =====================================================

def autenticar(usuario, contrasena):
    """
    Devuelve el dict del usuario si las credenciales son correctas
    y la cuenta está activa. En caso contrario, devuelve None.
    """
    db = SessionLocal()
    try:
        usuario = (usuario or "").strip()
        u = db.query(Usuario).filter(Usuario.usuario == usuario).first()

        if not u:
            return None
        if not u.activo:
            return None
        if not _verificar_contrasena(contrasena or "", u.contrasena_hash):
            return None

        return _a_dict(u)
    finally:
        db.close()


# =====================================================
# CREAR USUARIO (LO REALIZA EL ADMINISTRADOR)
# =====================================================

def crear_usuario(datos):
    """
    Crea un usuario con rol 'secretaria'. Solo el administrador
    gestiona la creación de estos usuarios desde Configuración.
    datos = {"usuario", "cedula", "contrasena"}
    """
    db = SessionLocal()
    try:
        usuario_nombre = _none(datos.get("usuario"))
        cedula = _none(datos.get("cedula"))
        contrasena = datos.get("contrasena") or ""

        if not usuario_nombre:
            return {"ok": False, "mensaje": "El nombre de usuario es obligatorio."}
        if not cedula:
            return {"ok": False, "mensaje": "La cédula es obligatoria."}
        if len(contrasena) < LONGITUD_MINIMA_CONTRASENA:
            return {"ok": False, "mensaje": f"La contraseña debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres."}

        if db.query(Usuario).filter(Usuario.usuario == usuario_nombre).first():
            return {"ok": False, "mensaje": "Ya existe un usuario con ese nombre de usuario."}
        if db.query(Usuario).filter(Usuario.cedula == cedula).first():
            return {"ok": False, "mensaje": "Ya existe un usuario registrado con esa cédula."}

        nuevo = Usuario(
            cedula=cedula,
            usuario=usuario_nombre,
            contrasena_hash=_hash_contrasena(contrasena),
            rol="secretaria",
            activo=bool(datos.get("activo", True)),
            fecha_registro=datetime.now(),
            fecha_actualizacion=datetime.now(),
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return {"ok": True, "mensaje": "Usuario registrado correctamente.", "id_usuario": nuevo.id_usuario}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al registrar el usuario: {e}"}
    finally:
        db.close()


# =====================================================
# ACTUALIZAR USUARIO (EL ADMIN EDITA A UNA SECRETARIA)
# =====================================================

def actualizar_usuario(id_usuario, datos):
    """
    Actualiza usuario/cédula/estado y, opcionalmente, la contraseña
    (si se envía 'contrasena' no vacía).
    """
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        if not u:
            return {"ok": False, "mensaje": "El usuario no existe."}

        usuario_nombre = _none(datos.get("usuario"))
        cedula = _none(datos.get("cedula"))
        contrasena = (datos.get("contrasena") or "").strip()

        if not usuario_nombre:
            return {"ok": False, "mensaje": "El nombre de usuario es obligatorio."}
        if not cedula:
            return {"ok": False, "mensaje": "La cédula es obligatoria."}

        duplicado_usuario = (
            db.query(Usuario)
            .filter(Usuario.usuario == usuario_nombre, Usuario.id_usuario != id_usuario)
            .first()
        )
        if duplicado_usuario:
            return {"ok": False, "mensaje": "Ya existe un usuario con ese nombre de usuario."}

        duplicado_cedula = (
            db.query(Usuario)
            .filter(Usuario.cedula == cedula, Usuario.id_usuario != id_usuario)
            .first()
        )
        if duplicado_cedula:
            return {"ok": False, "mensaje": "Ya existe un usuario registrado con esa cédula."}

        if contrasena:
            if len(contrasena) < LONGITUD_MINIMA_CONTRASENA:
                return {"ok": False, "mensaje": f"La contraseña debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres."}
            u.contrasena_hash = _hash_contrasena(contrasena)

        u.usuario = usuario_nombre
        u.cedula = cedula
        u.activo = bool(datos.get("activo", True))
        u.fecha_actualizacion = datetime.now()

        db.commit()
        return {"ok": True, "mensaje": "Usuario actualizado correctamente."}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al actualizar el usuario: {e}"}
    finally:
        db.close()


# =====================================================
# ELIMINAR USUARIO
# =====================================================

def eliminar_usuario(id_usuario):
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        if not u:
            return {"ok": False, "mensaje": "El usuario no existe."}
        if u.rol == "admin":
            return {"ok": False, "mensaje": "No se puede eliminar al usuario administrador."}

        db.delete(u)
        db.commit()
        return {"ok": True, "mensaje": "Usuario eliminado correctamente."}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al eliminar el usuario: {e}"}
    finally:
        db.close()


# =====================================================
# CAMBIO DE CONTRASEÑA POR CÉDULA
# =====================================================
# Se usa tanto desde "Olvidé mi contraseña" (login) como desde
# "Mi cuenta" dentro de Configuración. En ambos casos se exige
# la cédula registrada como verificación de identidad.

def cambiar_contrasena_por_cedula(usuario, cedula, nueva_contrasena):
    db = SessionLocal()
    try:
        usuario = (usuario or "").strip()
        cedula = (cedula or "").strip()
        nueva_contrasena = nueva_contrasena or ""

        u = db.query(Usuario).filter(Usuario.usuario == usuario).first()
        if not u:
            return {"ok": False, "mensaje": "No existe ningún usuario con ese nombre de usuario."}

        if not u.activo:
            return {"ok": False, "mensaje": "Esta cuenta se encuentra inactiva."}

        if (u.cedula or "").strip() != cedula:
            return {"ok": False, "mensaje": "La cédula no coincide con la registrada para este usuario."}

        if len(nueva_contrasena) < LONGITUD_MINIMA_CONTRASENA:
            return {"ok": False, "mensaje": f"La nueva contraseña debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres."}

        u.contrasena_hash = _hash_contrasena(nueva_contrasena)
        u.fecha_actualizacion = datetime.now()
        db.commit()
        return {"ok": True, "mensaje": "Contraseña actualizada correctamente."}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al cambiar la contraseña: {e}"}
    finally:
        db.close()


# =====================================================
# ACTUALIZAR MI PROPIO NOMBRE DE USUARIO
# =====================================================

def actualizar_mi_usuario(id_usuario, nuevo_usuario):
    db = SessionLocal()
    try:
        nuevo_usuario = _none(nuevo_usuario)
        if not nuevo_usuario:
            return {"ok": False, "mensaje": "El nombre de usuario es obligatorio."}

        u = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        if not u:
            return {"ok": False, "mensaje": "El usuario no existe."}

        duplicado = (
            db.query(Usuario)
            .filter(Usuario.usuario == nuevo_usuario, Usuario.id_usuario != id_usuario)
            .first()
        )
        if duplicado:
            return {"ok": False, "mensaje": "Ya existe un usuario con ese nombre de usuario."}

        u.usuario = nuevo_usuario
        u.fecha_actualizacion = datetime.now()
        db.commit()
        return {"ok": True, "mensaje": "Nombre de usuario actualizado correctamente.", "usuario": nuevo_usuario}
    except Exception as e:
        db.rollback()
        return {"ok": False, "mensaje": f"Error al actualizar el nombre de usuario: {e}"}
    finally:
        db.close()
