import tkinter as tk
from tkinter import messagebox

from ui.header import Header
from ui.sidebar import Sidebar
from ui import sesion

from ui.Modulos.Medicos.vista_medicos import VistaMedicos
from ui.Modulos.Inicio.vista_inicio import VistaInicio
from ui.Modulos.Guardias.vista_guardias import VistaGuardias
from ui.Modulos.Oficios.vista_oficios import VistaOficios
from ui.Modulos.Direccion.vista_direccion import VistaDireccion
from ui.Modulos.Configuracion.vista_configuracion import VistaConfiguracion


class VentanaPrincipal:

    def __init__(self, root, usuario_actual=None, al_cerrar_sesion=None):

        self.root = root
        self.al_cerrar_sesion = al_cerrar_sesion

        # Guarda el usuario que inició sesión en la sesión global,
        # para que cualquier módulo pueda consultar su rol.
        if usuario_actual:
            sesion.iniciar_sesion(usuario_actual)

        self.root.title(
            "Sistema de Gestión Hospitalaria"
        )

        self.root.state(
            "zoomed"
        )

        # CONTENEDOR GENERAL
        self.general = tk.Frame(root)

        self.general.pack(
            fill="both",
            expand=True
        )

        # SIDEBAR A LA IZQUIERDA
        self.sidebar = Sidebar(
            self.general,
            self.mostrar_inicio,
            self.mostrar_medicos,
            self.mostrar_guardias,
            self.mostrar_oficios,
            self.mostrar_direccion,
            self.mostrar_configuracion,
            self.cerrar_sesion,
            self.salir
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        # ZONA DERECHA
        self.derecha = tk.Frame(
            self.general
        )

        self.derecha.pack(
            side="right",
            fill="both",
            expand=True
        )

        # HEADER
        self.header = Header(
            self.derecha,
            usuario_actual=usuario_actual
        )

        self.header.pack(
            fill="x"
        )

        # CONTENIDO
        self.contenido = tk.Frame(
            self.derecha,
            bg="#EEF2F7"
        )

        self.contenido.pack(
            fill="both",
            expand=True
        )

        self.mostrar_inicio()

    def limpiar_contenido(self):

        for widget in self.contenido.winfo_children():
            widget.destroy()

    def mostrar_inicio(self):

        self.limpiar_contenido()

        VistaInicio(
            self.contenido,
            mostrar_medicos=self.mostrar_medicos,
            mostrar_guardias=self.mostrar_guardias,
            mostrar_oficios=self.mostrar_oficios,
            mostrar_direccion=self.mostrar_direccion
        ).pack(
            fill="both",
            expand=True
        )

    def mostrar_medicos(self, filtro="todos"):

        self.limpiar_contenido()

        VistaMedicos(
            self.contenido,
            filtro_inicial=filtro
        ).pack(
            fill="both",
            expand=True
        )

    def mostrar_guardias(self):

        self.limpiar_contenido()

        VistaGuardias(
            self.contenido
        ).pack(
            fill="both",
            expand=True
        )

    def mostrar_oficios(self):

        self.limpiar_contenido()

        VistaOficios(
            self.contenido
        ).pack(
            fill="both",
            expand=True
        )

    # ==============================
    # NUEVO MÓDULO: DIRECCIÓN
    # ==============================
    def mostrar_direccion(self):

        self.limpiar_contenido()

        VistaDireccion(
            self.contenido
        ).pack(
            fill="both",
            expand=True
        )

    # ==============================
    # NUEVO MÓDULO: CONFIGURACIÓN
    # ==============================
    def mostrar_configuracion(self):

        self.limpiar_contenido()

        VistaConfiguracion(
            self.contenido
        ).pack(
            fill="both",
            expand=True
        )

    # ==============================
    # CERRAR SESIÓN
    # ==============================
    def cerrar_sesion(self):

        respuesta = messagebox.askyesno(
            "Cerrar sesión",
            "¿Está seguro de que desea cerrar la sesión actual?",
            parent=self.root
        )

        if not respuesta:
            return

        sesion.cerrar_sesion()
        self.root.destroy()

        if self.al_cerrar_sesion:
            self.al_cerrar_sesion()

    # ==============================
    # SALIR
    # ==============================
    def salir(self):

        respuesta = messagebox.askyesno(
            "Salir",
            "¿Está seguro de que desea salir del sistema?",
            parent=self.root
        )

        if respuesta:
            self.root.destroy()
