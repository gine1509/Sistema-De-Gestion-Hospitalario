import tkinter as tk
import customtkinter as ctk
import re

from .colores import (
    COLOR_FONDO,
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
    COLOR_ROJO,
)

from ui.iconos import obtener_icono
from ui.mensajes import mostrar_exito, mostrar_error

from services.usuario_service import (
    crear_usuario,
    actualizar_usuario,
    buscar_por_usuario,
    buscar_por_cedula,
    LONGITUD_MINIMA_CONTRASENA,
)


class VentanaFormularioUsuario(ctk.CTkToplevel):
    """
    Ventana para que el administrador agregue o edite un usuario
    de rol secretaria: nombre de usuario, cédula y contraseña
    (la contraseña la asigna el propio administrador).
    """

    def __init__(self, parent, usuario=None, al_guardar=None):
        super().__init__(parent)

        self.parent = parent
        self.usuario = usuario
        self.al_guardar = al_guardar

        self.title("Editar usuario" if usuario else "Agregar usuario")
        self.geometry("200x400")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)

        self.transient(parent)
        self.grab_set()

        self.icono_usuario = obtener_icono("agregar_personal", 28)
        self.icono_guardar = obtener_icono("guardar", 18)
        self.icono_cancelar = obtener_icono("cancelar", 18)

        self._crear_interfaz()

        if self.usuario:
            self._cargar_datos_usuario()

        self.after(10, self._centrar)

    # =====================================================
    # CENTRAR
    # =====================================================

    def _centrar(self):
        self.update_idletasks()
        ancho = 560
        alto = min(620, self.winfo_screenheight() - 100)
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # =====================================================
    # INTERFAZ
    # =====================================================

    def _crear_interfaz(self):
        self._crear_header()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        self._crear_campos(scroll)
        self._crear_estado(scroll)

        self._crear_botones()

    def _crear_header(self):
        header = tk.Frame(self, bg=COLOR_AZUL, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        fila = tk.Frame(header, bg=COLOR_AZUL)
        fila.pack(anchor="w", padx=25, pady=(15, 0))

        if self.icono_usuario:
            tk.Label(fila, image=self.icono_usuario, bg=COLOR_AZUL).pack(side="left", padx=(0, 8))

        titulo = "Editar usuario" if self.usuario else "Agregar usuario"
        tk.Label(
            fila, text=titulo, font=("Segoe UI", 18, "bold"),
            fg="white", bg=COLOR_AZUL
        ).pack(side="left")

        tk.Label(
            header, text="Cuenta de acceso para rol Secretaria",
            font=("Segoe UI", 11), fg="#DCE8FF", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25)

    # =====================================================
    # TARJETA / CAMPO (mismo patrón que el resto de módulos)
    # =====================================================

    def _crear_tarjeta(self, parent, titulo):
        tarjeta = tk.Frame(
            parent, bg=COLOR_BLANCO,
            highlightbackground="#CBD5E1", highlightthickness=2,
            padx=10, pady=10
        )
        tarjeta.pack(fill="x", pady=(0, 12))

        tk.Label(
            tarjeta, text=titulo, font=("Segoe UI", 12, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_BLANCO
        ).pack(anchor="w", padx=15, pady=(15, 10))

        contenido = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        contenido.pack(fill="x", padx=15, pady=(0, 15))
        return contenido

    def _campo(self, parent, texto, secreto=False):
        frame = tk.Frame(parent, bg=COLOR_BLANCO)
        tk.Label(
            frame, text=texto, font=("Segoe UI", 10, "bold"),
            bg=COLOR_BLANCO, fg=COLOR_TEXTO
        ).pack(anchor="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            frame, height=42, fg_color="#FFFFFF",
            border_color="#64748B", border_width=2,
            text_color="#0F172A", placeholder_text_color="#64748B",
            corner_radius=8, show="•" if secreto else ""
        )
        entry.pack(fill="x")

        label_error = tk.Label(
            frame, text="", font=("Segoe UI", 9),
            fg=COLOR_ROJO, bg=COLOR_BLANCO
        )
        label_error.pack(anchor="w", pady=(3, 0))
        entry.label_error = label_error

        entry.bind("<KeyRelease>", lambda e, ent=entry: self._normal_entry(ent), add="+")
        return frame, entry

    def _error_entry(self, entry, mensaje=""):
        entry.configure(border_color=COLOR_ROJO)
        if hasattr(entry, "label_error"):
            entry.label_error.configure(text=mensaje)

    def _normal_entry(self, entry):
        entry.configure(border_color="#64748B")
        if hasattr(entry, "label_error"):
            entry.label_error.configure(text="")

    # =====================================================
    # CAMPOS
    # =====================================================

    def _crear_campos(self, parent):
        tarjeta = self._crear_tarjeta(parent, "Datos de la cuenta")

        campo, self.entry_usuario = self._campo(tarjeta, "Nombre de usuario *")
        campo.pack(fill="x", pady=5)
        self.entry_usuario.bind("<KeyRelease>", self._limpiar_usuario, add="+")

        campo, self.entry_cedula = self._campo(tarjeta, "Cédula *")
        campo.pack(fill="x", pady=5)
        self.entry_cedula.insert(0, "V-")
        self.entry_cedula.bind("<KeyRelease>", self._validar_cedula, add="+")

        campo, self.entry_rol = self._campo(tarjeta, "Rol")
        campo.pack(fill="x", pady=5)
        self.entry_rol.insert(0, "Secretaria")
        self.entry_rol.configure(state="disabled")

        titulo_pass = "Nueva contraseña (dejar vacío para no cambiarla)" if self.usuario else "Contraseña asignada *"
        campo, self.entry_contrasena = self._campo(tarjeta, titulo_pass, secreto=True)
        campo.pack(fill="x", pady=5)

        campo, self.entry_confirmar = self._campo(tarjeta, "Confirmar contraseña", secreto=True)
        campo.pack(fill="x", pady=5)

    def _crear_estado(self, parent):
        tarjeta = self._crear_tarjeta(parent, "Estado")

        fila_estado = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        fila_estado.pack(anchor="w", pady=5)

        self.label_estado = tk.Label(
            fila_estado, text="Activo", font=("Segoe UI", 11, "bold"),
            fg="#16A34A", bg=COLOR_BLANCO
        )
        self.label_estado.pack(side="left", padx=(0, 10))

        self.switch_activo = ctk.CTkSwitch(
            fila_estado, text="", width=50, height=24,
            fg_color="#CBD5E1", progress_color="#16A34A",
            button_color="white", button_hover_color="#F8FAFC",
            command=self._cambio_estado
        )
        self.switch_activo.select()
        self.switch_activo.pack(side="left")

        tk.Label(
            tarjeta,
            text="Un usuario inactivo no podrá iniciar sesión en el sistema.",
            font=("Segoe UI", 9), fg=COLOR_SECUNDARIO, bg=COLOR_BLANCO,
            wraplength=480, justify="left"
        ).pack(anchor="w", pady=(8, 0))

    def _cambio_estado(self):
        if self.switch_activo.get():
            self.label_estado.configure(text="Activo", fg="#16A34A")
        else:
            self.label_estado.configure(text="Inactivo", fg="#DC2626")

    # =====================================================
    # BOTONES
    # =====================================================

    def _crear_botones(self):
        botones = tk.Frame(self, bg=COLOR_FONDO)
        botones.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            botones, text="Cancelar", image=self.icono_cancelar, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color="#6C757D", hover_color="#4B5563",
            corner_radius=10, cursor="hand2", height=44, width=160,
            command=self.destroy
        ).pack(side="left")

        texto_btn = "Actualizar usuario" if self.usuario else "Guardar usuario"
        ctk.CTkButton(
            botones, text=texto_btn, image=self.icono_guardar, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color=COLOR_AZUL_HOVER, hover_color=COLOR_AZUL,
            corner_radius=10, cursor="hand2", height=44, width=190,
            command=self.guardar
        ).pack(side="right")

    # =====================================================
    # VALIDACIONES EN VIVO
    # =====================================================

    def _limpiar_usuario(self, event=None):
        valor = self.entry_usuario.get()
        limpio = "".join(c for c in valor if c.isalnum() or c in "._-")
        if limpio != valor:
            cursor = self.entry_usuario.index("insert")
            self.entry_usuario.delete(0, "end")
            self.entry_usuario.insert(0, limpio)
            try:
                self.entry_usuario.icursor(cursor)
            except Exception:
                pass

    def _validar_cedula(self, event=None):
        valor = self.entry_cedula.get()
        numeros = "".join(c for c in valor if c.isdigit())[:8]
        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, f"V-{numeros}")

    # =====================================================
    # CARGAR DATOS (MODO EDICIÓN)
    # =====================================================

    def _cargar_datos_usuario(self):
        u = self.usuario
        self.entry_usuario.insert(0, u.get("usuario", ""))
        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, u.get("cedula", "V-"))

        if u.get("activo", True):
            self.switch_activo.select()
        else:
            self.switch_activo.deselect()
        self._cambio_estado()

    # =====================================================
    # VALIDAR Y GUARDAR
    # =====================================================

    def guardar(self):
        self._normal_entry(self.entry_usuario)
        self._normal_entry(self.entry_cedula)
        self._normal_entry(self.entry_contrasena)
        self._normal_entry(self.entry_confirmar)

        usuario_nombre = self.entry_usuario.get().strip()
        cedula = self.entry_cedula.get().strip()
        contrasena = self.entry_contrasena.get()
        confirmar = self.entry_confirmar.get()

        hay_error = False

        # ---------- USUARIO ----------
        if not usuario_nombre:
            self._error_entry(self.entry_usuario, "El nombre de usuario es obligatorio.")
            hay_error = True
        elif len(usuario_nombre) < 4:
            self._error_entry(self.entry_usuario, "Debe tener al menos 4 caracteres.")
            hay_error = True
        else:
            existente = buscar_por_usuario(usuario_nombre)
            id_actual = self.usuario.get("id_usuario") if self.usuario else None
            if existente and existente["id_usuario"] != id_actual:
                self._error_entry(self.entry_usuario, "Este nombre de usuario ya está en uso.")
                hay_error = True

        # ---------- CÉDULA ----------
        if not cedula or cedula == "V-":
            self._error_entry(self.entry_cedula, "La cédula es obligatoria.")
            hay_error = True
        elif not re.match(r"^V-\d{6,8}$", cedula):
            self._error_entry(self.entry_cedula, "Formato de cédula inválido (Ej: V-12345678).")
            hay_error = True
        else:
            existente = buscar_por_cedula(cedula)
            id_actual = self.usuario.get("id_usuario") if self.usuario else None
            if existente and existente["id_usuario"] != id_actual:
                self._error_entry(self.entry_cedula, "Ya existe un usuario registrado con esta cédula.")
                hay_error = True

        # ---------- CONTRASEÑA ----------
        if not self.usuario and not contrasena:
            self._error_entry(self.entry_contrasena, "Debes asignar una contraseña.")
            hay_error = True
        elif contrasena and len(contrasena) < LONGITUD_MINIMA_CONTRASENA:
            self._error_entry(
                self.entry_contrasena,
                f"Debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres."
            )
            hay_error = True
        elif contrasena and contrasena != confirmar:
            self._error_entry(self.entry_confirmar, "Las contraseñas no coinciden.")
            hay_error = True

        if hay_error:
            return

        datos = {
            "usuario": usuario_nombre,
            "cedula": cedula,
            "contrasena": contrasena,
            "activo": bool(self.switch_activo.get()),
        }

        if self.usuario:
            resultado = actualizar_usuario(self.usuario["id_usuario"], datos)
            titulo_mensaje = "Usuario actualizado"
        else:
            resultado = crear_usuario(datos)
            titulo_mensaje = "Usuario registrado"

        if resultado["ok"]:
            mostrar_exito(self, titulo_mensaje, resultado.get("mensaje", "La operación se realizó con éxito."))
            self.destroy()
            if self.al_guardar:
                self.al_guardar()
        else:
            mostrar_error(self, "Error", resultado["mensaje"])
