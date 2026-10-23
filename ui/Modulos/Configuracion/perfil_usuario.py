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
    COLOR_VERDE,
    COLOR_ROJO,
)

from ui.iconos import obtener_icono


class VentanaPerfilUsuario(ctk.CTkToplevel):

    def __init__(self, vista, usuario):
        super().__init__(vista)

        self.vista = vista
        self.usuario = usuario

        self.title("Perfil del usuario")
        self.geometry("460x480")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)

        self.transient(vista)
        self.grab_set()

        self.icono_editar = obtener_icono("editar", 18)
        self.icono_eliminar = obtener_icono("eliminar", 18)
        self.icono_usuarios = obtener_icono("usuarios", 28)

        self._crear_interfaz()

        self.after(10, self._centrar)

    def _centrar(self):
        if not self.winfo_exists():
            return
        self.update_idletasks()
        ancho, alto = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # =====================================================
    # INTERFAZ
    # =====================================================

    def _crear_interfaz(self):
        header = tk.Frame(self, bg=COLOR_AZUL, height=110)
        header.pack(fill="x")
        header.pack_propagate(False)

        fila = tk.Frame(header, bg=COLOR_AZUL)
        fila.pack(anchor="w", padx=25, pady=(20, 0))

        if self.icono_usuarios:
            tk.Label(fila, image=self.icono_usuarios, bg=COLOR_AZUL).pack(side="left", padx=(0, 10))

        tk.Label(
            fila, text=self.usuario.get("usuario", ""), font=("Segoe UI", 18, "bold"),
            fg="white", bg=COLOR_AZUL
        ).pack(side="left")

        tk.Label(
            header, text="Cuenta de acceso - Rol Secretaría",
            font=("Segoe UI", 11), fg="#DCE8FF", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25)

        contenido = tk.Frame(self, bg=COLOR_FONDO)
        contenido.pack(fill="both", expand=True, padx=20, pady=20)

        tarjeta = tk.Frame(
            contenido, bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE, highlightthickness=1
        )
        tarjeta.pack(fill="x")

        self._dato(tarjeta, "Nombre de usuario", self.usuario.get("usuario", ""))
        self._dato(tarjeta, "Cédula", self.usuario.get("cedula", ""))
        self._dato(tarjeta, "Rol", "Secretaria")

        activo = self.usuario.get("activo", True)
        color_estado = COLOR_VERDE if activo else COLOR_ROJO
        texto_estado = "ACTIVO" if activo else "INACTIVO"

        fila_estado = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        fila_estado.pack(fill="x", padx=18, pady=(6, 18))
        tk.Label(
            fila_estado, text="Estado:", font=("Segoe UI", 10, "bold"),
            fg=COLOR_SECUNDARIO, bg=COLOR_BLANCO
        ).pack(side="left")
        tk.Label(
            fila_estado, text=texto_estado, font=("Segoe UI", 10, "bold"),
            fg=color_estado, bg=COLOR_BLANCO
        ).pack(side="left", padx=(6, 0))

        # ------------------------------------------------
        # BOTONES
        # ------------------------------------------------

        botones = tk.Frame(self, bg=COLOR_FONDO)
        botones.pack(fill="x", padx=20, pady=(0, 20))

        btn_eliminar = ctk.CTkButton(
            botones, text="Eliminar", image=self.icono_eliminar, compound="left",
            font=("Segoe UI", 12, "bold"), text_color="white",
            fg_color=COLOR_ROJO, hover_color="#B91C1C",
            corner_radius=10, cursor="hand2", height=42, width=140,
            command=self._eliminar
        )
        btn_eliminar.pack(side="left")

        btn_editar = ctk.CTkButton(
            botones, text="Editar", image=self.icono_editar, compound="left",
            font=("Segoe UI", 12, "bold"), text_color="white",
            fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
            corner_radius=10, cursor="hand2", height=42, width=140,
            command=self._editar
        )
        btn_editar.pack(side="right")

    def _dato(self, parent, etiqueta, valor):
        fila = tk.Frame(parent, bg=COLOR_BLANCO)
        fila.pack(fill="x", padx=18, pady=(14, 0))
        tk.Label(
            fila, text=etiqueta, font=("Segoe UI", 9), fg=COLOR_SECUNDARIO, bg=COLOR_BLANCO
        ).pack(anchor="w")
        tk.Label(
            fila, text=valor or "No registrado", font=("Segoe UI", 12, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_BLANCO
        ).pack(anchor="w")

    def _editar(self):
        self.destroy()
        self.vista.editar_usuario(self.usuario)

    def _eliminar(self):
        self.destroy()
        self.vista.eliminar_usuario(self.usuario)
