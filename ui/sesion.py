

usuario_actual = None  # dict: {id_usuario, cedula, usuario, rol, activo}


def iniciar_sesion(usuario):
    global usuario_actual
    usuario_actual = usuario


def cerrar_sesion():
    global usuario_actual
    usuario_actual = None


def obtener_usuario_actual():
    return usuario_actual


def rol_actual():
    return usuario_actual.get("rol") if usuario_actual else None


def es_admin():
    return rol_actual() == "admin"


def nombre_usuario_actual():
    return usuario_actual.get("usuario") if usuario_actual else ""
