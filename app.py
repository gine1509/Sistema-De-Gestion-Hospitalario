import os
import sys
import tkinter as tk

from ui.ventana_login import VentanaLogin
from ui.ventana_principal import VentanaPrincipal
from services.usuario_service import asegurar_usuario_admin

def obtener_ruta_recurso(ruta_relativa):
    """
    Obtiene la ruta absoluta para recursos (imágenes, plantillas, iconos),
    compatible con ejecución normal en Python y empaquetado con PyInstaller.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, ruta_relativa)

# Construye la ruta exacta hacia el icono
RUTA_ICONO = obtener_ruta_recurso(os.path.join("iconos", "hospital.ico"))

asegurar_usuario_admin()

def ejecutar_aplicacion():
    while True:

        # ------------------------------------------------
        # PANTALLA DE LOGIN
        # ------------------------------------------------
        sesion_iniciada = {}

        def manejar_login(usuario_autenticado):
            sesion_iniciada.update(usuario_autenticado)
            login_root.quit()

        login_root = tk.Tk()
        if os.path.exists(RUTA_ICONO):
            login_root.iconbitmap(RUTA_ICONO)

        VentanaLogin(login_root, al_iniciar_sesion=manejar_login)
        login_root.mainloop()

        try:
            login_root.destroy()
        except tk.TclError:
            pass

        if not sesion_iniciada:
            break

        # ------------------------------------------------
        # VENTANA PRINCIPAL
        # ------------------------------------------------
        cerro_sesion = {"valor": False}

        def manejar_cerrar_sesion():
            cerro_sesion["valor"] = True

        root = tk.Tk()
        if os.path.exists(RUTA_ICONO):
            root.iconbitmap(RUTA_ICONO)

        VentanaPrincipal(
            root,
            usuario_actual=sesion_iniciada,
            al_cerrar_sesion=manejar_cerrar_sesion
        )
        root.mainloop()

        try:
            root.destroy()
        except tk.TclError:
            pass

        if not cerro_sesion["valor"]:
            break

if __name__ == "__main__":
    ejecutar_aplicacion()