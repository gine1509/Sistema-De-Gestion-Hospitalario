import tkinter as tk
import customtkinter as ctk

from .colores import (
    COLOR_FONDO,
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_BORDE,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
    COLOR_ROJO,
)

from ui.iconos import obtener_icono
from ui.mensajes import mostrar_exito, mostrar_error
from ui import sesion

from services.usuario_service import (
    actualizar_mi_usuario,
    cambiar_contrasena_por_cedula,
    LONGITUD_MINIMA_CONTRASENA,
)


class VentanaMiCuenta(ctk.CTkToplevel):
    """
    Permite al usuario que inició sesión (admin o secretaria) cambiar
    su propio nombre de usuario y su contraseña. El cambio de
    contraseña siempre exige la cédula registrada como verificación,
    ya que el sistema no maneja "contraseña actual".
    """

    def __init__(self, parent, al_actualizar=None):
        super().__init__(parent)

        self.parent = parent
        self.al_actualizar = al_actualizar
        self.usuario_actual = sesion.obtener_usuario_actual() or {}

        self.title("Mi cuenta")
        self.geometry("500x560")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)

        self.transient(parent)
        self.grab_set()

        self.icono_guardar = obtener_icono("guardar", 18)
        self.icono_usuario = obtener_icono("informacion_personal", 26)

        self._crear_interfaz()

        self.after(10, self._centrar)

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 500, 560
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # =====================================================
    # INTERFAZ
    # =====================================================

    def _crear_interfaz(self):
        header = tk.Frame(self, bg=COLOR_AZUL, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        fila = tk.Frame(header, bg=COLOR_AZUL)
        fila.pack(anchor="w", padx=25, pady=(15, 0))
        if self.icono_usuario:
            tk.Label(fila, image=self.icono_usuario, bg=COLOR_AZUL).pack(side="left", padx=(0, 8))
        tk.Label(
            fila, text="Mi cuenta", font=("Segoe UI", 18, "bold"),
            fg="white", bg=COLOR_AZUL
        ).pack(side="left")

        tk.Label(
            header, text=f"Cédula registrada: {self.usuario_actual.get('cedula', '')}",
            font=("Segoe UI", 11), fg="#DCE8FF", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        self._crear_seccion_usuario(scroll)
        self._crear_seccion_contrasena(scroll)

    def _crear_tarjeta(self, parent, titulo, subtitulo=""):
        tarjeta = tk.Frame(
            parent, bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE, highlightthickness=2,
            padx=10, pady=10
        )
        tarjeta.pack(fill="x", pady=(0, 15))

        tk.Label(
            tarjeta, text=titulo, font=("Segoe UI", 12, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_BLANCO
        ).pack(anchor="w", padx=15, pady=(15, 2))

        if subtitulo:
            tk.Label(
                tarjeta, text=subtitulo, font=("Segoe UI", 9),
                fg=COLOR_SECUNDARIO, bg=COLOR_BLANCO, wraplength=420, justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 8))

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
            frame, height=40, fg_color="#FFFFFF",
            border_color="#64748B", border_width=2,
            text_color="#0F172A", corner_radius=8,
            show="•" if secreto else ""
        )
        entry.pack(fill="x")

        label_error = tk.Label(frame, text="", font=("Segoe UI", 9), fg=COLOR_ROJO, bg=COLOR_BLANCO)
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
    # SECCIÓN: CAMBIAR NOMBRE DE USUARIO
    # =====================================================

    def _crear_seccion_usuario(self, parent):
        contenido = self._crear_tarjeta(parent, "Nombre de usuario")

        campo, self.entry_usuario = self._campo(contenido, "Usuario *")
        campo.pack(fill="x", pady=(0, 10))
        self.entry_usuario.insert(0, self.usuario_actual.get("usuario", ""))

        ctk.CTkButton(
            contenido, text="Actualizar usuario", image=self.icono_guardar, compound="left",
            font=("Segoe UI", 12, "bold"), text_color="white",
            fg_color=COLOR_AZUL_HOVER, hover_color=COLOR_AZUL,
            corner_radius=10, cursor="hand2", height=40,
            command=self._actualizar_usuario
        ).pack(anchor="e")

    def _actualizar_usuario(self):
        self._normal_entry(self.entry_usuario)
        nuevo_usuario = self.entry_usuario.get().strip()

        if not nuevo_usuario or len(nuevo_usuario) < 4:
            self._error_entry(self.entry_usuario, "Debe tener al menos 4 caracteres.")
            return

        resultado = actualizar_mi_usuario(self.usuario_actual["id_usuario"], nuevo_usuario)

        if resultado["ok"]:
            self.usuario_actual["usuario"] = resultado["usuario"]
            sesion.iniciar_sesion(self.usuario_actual)
            mostrar_exito(self, "Usuario actualizado", resultado["mensaje"])
            if self.al_actualizar:
                self.al_actualizar()
        else:
            self._error_entry(self.entry_usuario, resultado["mensaje"])

    # =====================================================
    # SECCIÓN: CAMBIAR CONTRASEÑA
    # =====================================================

    def _crear_seccion_contrasena(self, parent):
        contenido = self._crear_tarjeta(
            parent, "Cambiar contraseña",
            "Por seguridad, confirma tu cédula registrada para poder cambiar la contraseña."
        )

        campo, self.entry_cedula = self._campo(contenido, "Cédula registrada *")
        campo.pack(fill="x", pady=(0, 10))
        self.entry_cedula.insert(0, "V-")
        self.entry_cedula.bind("<KeyRelease>", self._validar_cedula, add="+")

        campo, self.entry_nueva = self._campo(contenido, "Nueva contraseña *", secreto=True)
        campo.pack(fill="x", pady=(0, 10))

        campo, self.entry_confirmar = self._campo(contenido, "Confirmar nueva contraseña *", secreto=True)
        campo.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            contenido, text="Cambiar contraseña", image=self.icono_guardar, compound="left",
            font=("Segoe UI", 12, "bold"), text_color="white",
            fg_color=COLOR_AZUL_HOVER, hover_color=COLOR_AZUL,
            corner_radius=10, cursor="hand2", height=40,
            command=self._cambiar_contrasena
        ).pack(anchor="e")

    def _validar_cedula(self, event=None):
        valor = self.entry_cedula.get()
        numeros = "".join(c for c in valor if c.isdigit())[:8]
        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, f"V-{numeros}")

    def _cambiar_contrasena(self):
        self._normal_entry(self.entry_cedula)
        self._normal_entry(self.entry_nueva)
        self._normal_entry(self.entry_confirmar)

        cedula = self.entry_cedula.get().strip()
        nueva = self.entry_nueva.get()
        confirmar = self.entry_confirmar.get()

        if not cedula or cedula == "V-":
            self._error_entry(self.entry_cedula, "La cédula es obligatoria.")
            return

        if not nueva or len(nueva) < LONGITUD_MINIMA_CONTRASENA:
            self._error_entry(self.entry_nueva, f"Debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres.")
            return

        if nueva != confirmar:
            self._error_entry(self.entry_confirmar, "Las contraseñas no coinciden.")
            return

        resultado = cambiar_contrasena_por_cedula(
            self.usuario_actual.get("usuario", ""), cedula, nueva
        )

        if resultado["ok"]:
            mostrar_exito(self, "Contraseña actualizada", resultado["mensaje"])
            self.entry_nueva.delete(0, "end")
            self.entry_confirmar.delete(0, "end")
        else:
            self._error_entry(self.entry_cedula, resultado["mensaje"])
