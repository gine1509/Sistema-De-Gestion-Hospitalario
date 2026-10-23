import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from ui.iconos import obtener_icono
from ui.mensajes import mostrar_pregunta, mostrar_error, mostrar_exito
from ui import sesion

from services.usuario_service import listar_usuarios, eliminar_usuario as servicio_eliminar_usuario

from .formulario_usuario import VentanaFormularioUsuario
from .perfil_usuario import VentanaPerfilUsuario
from .cuenta_usuario import VentanaMiCuenta

COLOR_FONDO = "#F4F7FB"
COLOR_BLANCO = "#FFFFFF"
COLOR_TEXTO = "#0F172A"
COLOR_SECUNDARIO = "#64748B"
COLOR_AZUL = "#2563EB"
COLOR_AZUL_HOVER = "#0B4F94"
COLOR_BORDE = "#D5DEE8"
COLOR_VERDE = "#16A34A"
COLOR_ROJO = "#DC2626"


class VistaConfiguracion(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_FONDO)

        self.usuario_actual = sesion.obtener_usuario_actual() or {}
        self.es_admin = sesion.es_admin()
        self.usuarios = []

        self._cargar_iconos()
        self.crear_interfaz()

        if self.es_admin:
            self.cargar_usuarios()

    def _cargar_iconos(self):
        self.icon_usuarios = obtener_icono("usuarios", 22)
        self.icon_agregar = obtener_icono("agregar", 18)
        self.icon_buscar = obtener_icono("buscar", 16)
        self.icon_ver = obtener_icono("ver", 16)
        self.icon_informacion_personal = obtener_icono("informacion_personal", 22)

    # =====================================================
    # INTERFAZ GENERAL
    # =====================================================

    def crear_interfaz(self):
        self.canvas = tk.Canvas(self, bg=COLOR_FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(self.canvas, bg=COLOR_FONDO)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._scroll)

        contenido = tk.Frame(self.scroll_frame, bg=COLOR_FONDO)
        contenido.pack(fill="both", expand=True, padx=35, pady=25)

        # ------------------------------------------------
        # ENCABEZADO
        # ------------------------------------------------

        bloque = tk.Frame(contenido, bg=COLOR_FONDO)
        bloque.pack(fill="x", pady=(0, 18), anchor="w")
        tk.Label(
            bloque, text="Configuración", bg=COLOR_FONDO, fg=COLOR_TEXTO,
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w")
        tk.Label(
            bloque,
            text="Gestiona tu cuenta de acceso"
                 + (" y los usuarios del sistema." if self.es_admin else "."),
            bg=COLOR_FONDO, fg=COLOR_SECUNDARIO, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(3, 0))

        # ------------------------------------------------
        # SECCIÓN: MI CUENTA
        # ------------------------------------------------

        self._crear_seccion_mi_cuenta(contenido)

        # ------------------------------------------------
        # SECCIÓN: GESTIÓN DE USUARIOS (SOLO ADMIN)
        # ------------------------------------------------

        if self.es_admin:
            separador = tk.Frame(contenido, bg="#E2E8F0", height=1)
            separador.pack(fill="x", pady=(30, 20))

            bloque_usuarios = tk.Frame(contenido, bg=COLOR_FONDO)
            bloque_usuarios.pack(fill="x", pady=(0, 14))
            tk.Label(
                bloque_usuarios, text="Usuarios del sistema (Secretaría)", bg=COLOR_FONDO,
                fg=COLOR_TEXTO, font=("Segoe UI", 20, "bold")
            ).pack(anchor="w")
            tk.Label(
                bloque_usuarios,
                text="Agrega, edita, elimina y visualiza las cuentas de acceso del personal de secretaría.",
                bg=COLOR_FONDO, fg=COLOR_SECUNDARIO, font=("Segoe UI", 10)
            ).pack(anchor="w", pady=(3, 0))

            self._crear_barra_usuarios(contenido)

            self.contador = tk.Label(
                contenido, text="", bg=COLOR_FONDO, fg=COLOR_SECUNDARIO, font=("Segoe UI", 11)
            )
            self.contador.pack(anchor="w", pady=(0, 12))

            self.lista = tk.Frame(contenido, bg=COLOR_FONDO)
            self.lista.pack(fill="both", expand=True)

    def _scroll(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # =====================================================
    # SECCIÓN: MI CUENTA
    # =====================================================

    def _crear_seccion_mi_cuenta(self, parent):
        tarjeta = tk.Frame(
            parent, bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE, highlightthickness=1
        )
        tarjeta.pack(fill="x")

        contenido_tarjeta = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        contenido_tarjeta.pack(fill="x", padx=22, pady=20)

        izquierda = tk.Frame(contenido_tarjeta, bg=COLOR_BLANCO)
        izquierda.pack(side="left", fill="x", expand=True)

        fila_titulo = tk.Frame(izquierda, bg=COLOR_BLANCO)
        fila_titulo.pack(anchor="w")

        if self.icon_informacion_personal:
            tk.Label(fila_titulo, image=self.icon_informacion_personal, bg=COLOR_BLANCO).pack(side="left", padx=(0, 8))

        tk.Label(
            fila_titulo, text="Mi cuenta", bg=COLOR_BLANCO, fg=COLOR_TEXTO,
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")

        rol_texto = "Administrador" if self.es_admin else "Secretaria"
        tk.Label(
            izquierda,
            text=f"Usuario: {self.usuario_actual.get('usuario', '')}   |   Cédula: {self.usuario_actual.get('cedula', '')}   |   Rol: {rol_texto}",
            bg=COLOR_BLANCO, fg=COLOR_SECUNDARIO, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(6, 0))

        ctk.CTkButton(
            contenido_tarjeta, text="Cambiar mi usuario o contraseña",
            font=("Segoe UI", 12, "bold"), text_color=COLOR_BLANCO,
            fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
            corner_radius=10, cursor="hand2", height=40, width=240,
            command=self.abrir_mi_cuenta
        ).pack(side="right")

    def abrir_mi_cuenta(self):
        VentanaMiCuenta(self, al_actualizar=self._refrescar_mi_cuenta)

    def _refrescar_mi_cuenta(self):
        # Redibuja toda la vista para reflejar el nuevo nombre de usuario.
        for widget in self.winfo_children():
            widget.destroy()
        self.usuario_actual = sesion.obtener_usuario_actual() or {}
        self.crear_interfaz()
        if self.es_admin:
            self.cargar_usuarios()

    # =====================================================
    # SECCIÓN: GESTIÓN DE USUARIOS (ADMIN)
    # =====================================================

    def _crear_barra_usuarios(self, parent):
        barra = tk.Frame(parent, bg=COLOR_FONDO)
        barra.pack(fill="x", pady=(0, 14))

        buscador = tk.Frame(barra, bg=COLOR_BLANCO, highlightbackground=COLOR_BORDE, highlightthickness=1)
        buscador.pack(side="left", fill="x", expand=True)

        if self.icon_buscar:
            tk.Label(buscador, image=self.icon_buscar, bg=COLOR_BLANCO).pack(side="left", padx=(12, 5), pady=8)

        self.busqueda = tk.Entry(buscador, bg=COLOR_BLANCO, fg="#94A3B8", relief="flat", font=("Segoe UI", 12))
        self.busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=9)
        self.placeholder = "Buscar por usuario o cédula..."
        self.busqueda.insert(0, self.placeholder)
        self.busqueda.bind("<FocusIn>", self._limpiar_placeholder)
        self.busqueda.bind("<KeyRelease>", lambda e: self.aplicar_busqueda())

        ctk.CTkButton(
            barra, text="Agregar usuario", image=self.icon_agregar, compound="left",
            width=175, height=40, corner_radius=8,
            fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
            font=("Segoe UI", 13, "bold"), command=self.agregar_usuario
        ).pack(side="right", padx=(10, 0))

    def _limpiar_placeholder(self, event):
        if self.busqueda.get() == self.placeholder:
            self.busqueda.delete(0, "end")
            self.busqueda.configure(fg=COLOR_TEXTO)

    def aplicar_busqueda(self):
        texto = self.busqueda.get().strip()
        if texto == self.placeholder:
            texto = ""
        self.pintar(listar_usuarios(texto, rol="secretaria"))

    def cargar_usuarios(self):
        try:
            self.usuarios = listar_usuarios(rol="secretaria")
        except Exception as e:
            print(f"[VistaConfiguracion] Error: {e}")
            self.usuarios = []
        self.pintar(self.usuarios)

    def pintar(self, usuarios):
        for w in self.lista.winfo_children():
            w.destroy()

        self.contador.configure(
            text=f"{len(usuarios)} usuario{'s' if len(usuarios) != 1 else ''} de secretaría"
        )

        for columna in range(3):
            self.lista.grid_columnconfigure(columna, weight=0)

        for i, usuario in enumerate(usuarios):
            fila = i // 3
            columna = i % 3
            self.crear_tarjeta(usuario, fila, columna)

    def crear_tarjeta(self, usuario, fila, columna):
        tarjeta = tk.Frame(
            self.lista, bg=COLOR_BLANCO, highlightbackground=COLOR_BORDE,
            highlightthickness=1, width=330, height=190
        )
        tarjeta.grid(row=fila, column=columna, sticky="nw", padx=7, pady=7)
        tarjeta.pack_propagate(False)

        activo = usuario.get("activo", True)
        color_estado = COLOR_VERDE if activo else COLOR_ROJO
        estado = "ACTIVO" if activo else "INACTIVO"

        top = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        top.pack(fill="x", padx=18, pady=(17, 6))

        icono_fondo = tk.Frame(top, bg=COLOR_AZUL, width=38, height=38)
        icono_fondo.pack(side="left", anchor="n")
        icono_fondo.pack_propagate(False)

        if self.icon_usuarios:
            icono_label = tk.Label(icono_fondo, image=self.icon_usuarios, bg=COLOR_AZUL)
            icono_label.image = self.icon_usuarios
            icono_label.place(relx=0.5, rely=0.5, anchor="center")

        info_top = tk.Frame(top, bg=COLOR_BLANCO)
        info_top.pack(side="left", fill="x", expand=True, padx=(10, 0))

        tk.Label(
            info_top, text=estado, bg=COLOR_BLANCO, fg=color_estado,
            font=("Segoe UI", 8, "bold")
        ).pack(side="right", anchor="ne")

        tk.Label(
            info_top, text=usuario["usuario"], bg=COLOR_BLANCO, fg=COLOR_TEXTO,
            font=("Segoe UI", 11, "bold"), wraplength=170, justify="left"
        ).pack(side="top", anchor="w")

        tk.Label(
            tarjeta, text="Rol: Secretaria", bg=COLOR_BLANCO, fg=COLOR_TEXTO,
            font=("Segoe UI", 9), justify="left"
        ).pack(anchor="w", padx=18, pady=(4, 0))

        tk.Label(
            tarjeta, text=f"Cédula: {usuario['cedula']}", bg=COLOR_BLANCO,
            fg=COLOR_SECUNDARIO, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(6, 0))

        separador = tk.Frame(tarjeta, bg="#EEF2F7", height=1)
        separador.pack(fill="x", padx=18, pady=(12, 12))

        pie = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        pie.pack(fill="x", padx=18, pady=(0, 15))

        ctk.CTkButton(
            pie, text="Ver perfil", image=self.icon_ver, compound="left",
            font=("Segoe UI", 12, "bold"), text_color=COLOR_BLANCO,
            fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
            corner_radius=10, cursor="hand2", height=38,
            command=lambda u=usuario: self.ver_perfil(u)
        ).pack(fill="x")

    # =====================================================
    # ACCIONES
    # =====================================================

    def agregar_usuario(self):
        VentanaFormularioUsuario(self, al_guardar=self.cargar_usuarios)

    def editar_usuario(self, usuario):
        VentanaFormularioUsuario(self, usuario=usuario, al_guardar=self.cargar_usuarios)

    def ver_perfil(self, usuario):
        VentanaPerfilUsuario(self, usuario)

    def eliminar_usuario(self, usuario):
        if not mostrar_pregunta(
            self, "Eliminar usuario",
            f"¿Deseas eliminar la cuenta del usuario \"{usuario['usuario']}\"?\n\nEsta acción no se puede deshacer."
        ):
            return

        resultado = servicio_eliminar_usuario(usuario["id_usuario"])
        if resultado["ok"]:
            mostrar_exito(self, "Usuario eliminado", resultado["mensaje"])
            self.cargar_usuarios()
        else:
            mostrar_error(self, "Error", resultado["mensaje"])
