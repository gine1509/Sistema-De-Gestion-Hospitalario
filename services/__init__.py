__all__ = [
    "listar_medicos",
    "obtener_medico",
    "buscar_por_cedula",
    "crear_medico",
    "actualizar_medico",
    "desactivar_medico",
    "activar_medico",
    "eliminar_medico",
    "listar_dependencias",
    "listar_tipos_contratacion",
    "listar_estatus",
]


def __getattr__(name):
    if name in __all__:
        from . import medico_services as _medico_services
        return getattr(_medico_services, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(__all__))