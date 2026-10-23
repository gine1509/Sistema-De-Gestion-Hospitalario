import tkinter as tk
import customtkinter as ctk

from ui.iconos import obtener_icono
from ui.mensajes import mostrar_error, mostrar_exito
from services.usuario_service import autenticar, cambiar_contrasena_por_cedula

COLOR_FONDO = "#F4F7FB"
COLOR_BLANCO = "#FFFFFF"
COLOR_TEXTO = "#0F172A"
COLOR_SECUNDARIO = "#64748B"
COLOR_AZUL = "#2563EB"
COLOR_AZUL_HOVER = "#0B4F94"
COLOR_BORDE = "#D5DEE8"
COLOR_ROJO = "#DC2626"


class VentanaLogin(tk.Frame):
    """
    Pantalla de inicio de sesión. Se monta directamente sobre el root
    de la aplicación (no es un Toplevel) porque es la primera pantalla
    que ve el usuario.
    """

    def __init__(self, root, al_iniciar_sesion):
        super().__init__(root, bg=COLOR_FONDO)

        self.root = root
        self.al_iniciar_sesion = al_iniciar_sesion

        self.root.title("Sistema Gestión Hospitalaria - Iniciar sesión")
        
        # --- Centrado dinámico de la ventana principal ---
        ancho, alto = 1000, 650
        self.root.minsize(900, 600)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

        self.pack(fill="both", expand=True)

        self.icono_candado = obtener_icono("configuracion", 34)
        self.icono_usuario = obtener_icono("usuarios", 18)

        self._crear_interfaz()

        self.root.bind("<Return>", lambda e: self.iniciar_sesion())

    # =====================================================
    # INTERFAZ
    # =====================================================

    def _crear_interfaz(self):
        # Panel izquierdo (marca / institución)
        panel_izquierdo = tk.Frame(self, bg=COLOR_AZUL_HOVER)
        panel_izquierdo.pack(side="left", fill="both", expand=True)

        contenedor_marca = tk.Frame(panel_izquierdo, bg=COLOR_AZUL_HOVER)
        contenedor_marca.place(relx=0.5, rely=0.5, anchor="center")

        try:
            self.logo_img = tk.PhotoImage(file="ui/Logos/logo_blanco.png")
            self.logo_img = self.logo_img.subsample(2, 2)
            tk.Label(contenedor_marca, image=self.logo_img, bg=COLOR_AZUL_HOVER).pack(pady=(0, 15))
        except Exception:
            pass

        tk.Label(
            contenedor_marca, text="Sistema de Gestión\nHospitalaria",
            bg=COLOR_AZUL_HOVER, fg="white", font=("Segoe UI", 26, "bold"),
            justify="center"
        ).pack()

        tk.Label(
            contenedor_marca, text="Departamento de Dirección",
            bg=COLOR_AZUL_HOVER, fg="#CBDCF6", font=("Segoe UI", 12)
        ).pack(pady=(6, 0))

        # Panel derecho (formulario)
        panel_derecho = tk.Frame(self, bg=COLOR_BLANCO, width=420)
        panel_derecho.pack(side="right", fill="y")
        panel_derecho.pack_propagate(False)

        contenedor = tk.Frame(panel_derecho, bg=COLOR_BLANCO)
        contenedor.place(relx=0.5, rely=0.5, anchor="center")

        if self.icono_candado:
            tk.Label(contenedor, image=self.icono_candado, bg=COLOR_BLANCO).pack(pady=(0, 10))

        tk.Label(
            contenedor, text="Iniciar sesión", bg=COLOR_BLANCO, fg=COLOR_TEXTO,
            font=("Segoe UI", 22, "bold")
        ).pack()

        tk.Label(
            contenedor, text="Ingresa tus credenciales para continuar",
            bg=COLOR_BLANCO, fg=COLOR_SECUNDARIO, font=("Segoe UI", 10)
        ).pack(pady=(2, 25))

        campo_usuario, self.entry_usuario = self._campo(contenedor, "Usuario *")
        campo_usuario.pack(fill="x", pady=(0, 12))

        campo_contrasena, self.entry_contrasena = self._campo(contenedor, "Contraseña *", secreto=True)
        campo_contrasena.pack(fill="x", pady=(0, 6))

        self.label_error_login = tk.Label(
            contenedor, text="", font=("Segoe UI", 9), fg=COLOR_ROJO, bg=COLOR_BLANCO,
            wraplength=300, justify="left"
        )
        self.label_error_login.pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(
            contenedor, text="Ingresar", height=44, width=320,
            corner_radius=8, fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
            font=("Segoe UI", 13, "bold"), command=self.iniciar_sesion
        ).pack(pady=(6, 14))

        enlace = tk.Label(
            contenedor, text="¿Olvidaste tu contraseña?", bg=COLOR_BLANCO,
            fg=COLOR_AZUL, font=("Segoe UI", 10, "bold"), cursor="hand2"
        )
        enlace.pack()
        enlace.bind("<Button-1>", lambda e: self.abrir_recuperar_contrasena())

    def _campo(self, parent, texto, secreto=False):
        frame = tk.Frame(parent, bg=COLOR_BLANCO, width=320)
        tk.Label(
            frame, text=texto, font=("Segoe UI", 10, "bold"),
            bg=COLOR_BLANCO, fg=COLOR_TEXTO
        ).pack(anchor="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            frame, height=42, width=320, fg_color="#FFFFFF",
            border_color="#64748B", border_width=2,
            text_color="#0F172A", corner_radius=8,
            show="•" if secreto else ""
        )
        entry.pack(fill="x")
        return frame, entry

    # =====================================================
    # INICIAR SESIÓN
    # =====================================================

    def iniciar_sesion(self):
        usuario = self.entry_usuario.get().strip()
        contrasena = self.entry_contrasena.get()

        if not usuario or not contrasena:
            self.label_error_login.configure(text="Debes ingresar usuario y contraseña.")
            return

        resultado = autenticar(usuario, contrasena)

        if not resultado:
            self.label_error_login.configure(text="Usuario o contraseña incorrectos.")
            return

        self.label_error_login.configure(text="")
        self.root.unbind("<Return>")
        self.al_iniciar_sesion(resultado)

    # =====================================================
    # RECUPERAR CONTRASEÑA
    # =====================================================

    def abrir_recuperar_contrasena(self):
        VentanaRecuperarContrasena(self.root, usuario_inicial=self.entry_usuario.get().strip())


class VentanaRecuperarContrasena(ctk.CTkToplevel):

    def __init__(self, parent, usuario_inicial=""):
        super().__init__(parent)

        self.parent = parent

        self.title("Recuperar contraseña")
        
        self.ancho = 440
        self.alto = 580
        self.geometry(f"{self.ancho}x{self.alto}")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)

        self.transient(parent)
        self.grab_set()

        self.icono_guardar = obtener_icono("guardar", 18)
        self.icono_cancelar = obtener_icono("cancelar", 18)

        self._crear_interfaz(usuario_inicial)

        # Capturamos el botón de cierre (X) de la ventana
        self.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

        self.after(10, self._centrar)

    def _centrar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.ancho // 2)
        y = (self.winfo_screenheight() // 2) - (self.alto // 2)
        self.geometry(f"{self.ancho}x{self.alto}+{x}+{y}")

    def cerrar_ventana(self):
        """Cierra la ventana limpiando las animaciones pendientes de CustomTkinter."""
        self.withdraw()
        self.update_idletasks()
        self.destroy()

    def _crear_interfaz(self, usuario_inicial):
        header = tk.Frame(self, bg=COLOR_AZUL, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="Recuperar contraseña", font=("Segoe UI", 18, "bold"),
            fg="white", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25, pady=(18, 0))

        tk.Label(
            header, text="Verifica tu identidad con tu cédula registrada",
            font=("Segoe UI", 10), fg="#DCE8FF", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25)

        contenido = tk.Frame(self, bg=COLOR_FONDO)
        contenido.pack(fill="both", expand=True, padx=25, pady=(15, 5))

        campo, self.entry_usuario = self._campo(contenido, "Usuario *")
        campo.pack(fill="x", pady=(0, 8))
        self.entry_usuario.insert(0, usuario_inicial)

        campo, self.entry_cedula = self._campo(contenido, "Cédula registrada *")
        campo.pack(fill="x", pady=(0, 8))
        self.entry_cedula.insert(0, "V-")
        self.entry_cedula.bind("<KeyRelease>", self._validar_cedula, add="+")

        campo, self.entry_nueva = self._campo(contenido, "Nueva contraseña *", secreto=True)
        campo.pack(fill="x", pady=(0, 8))

        campo, self.entry_confirmar = self._campo(contenido, "Confirmar nueva contraseña *", secreto=True)
        campo.pack(fill="x", pady=(0, 4))

        self.label_error = tk.Label(
            contenido, text="", font=("Segoe UI", 9), fg=COLOR_ROJO, bg=COLOR_FONDO,
            wraplength=380, justify="left"
        )
        self.label_error.pack(anchor="w", pady=(0, 5))

        botones = tk.Frame(self, bg=COLOR_FONDO)
        botones.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            botones, text="Cancelar", image=self.icono_cancelar, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color="#6C757D", hover_color="#4B5563",
            corner_radius=10, cursor="hand2", height=44, width=130,
            command=self.cerrar_ventana
        ).pack(side="left")

        ctk.CTkButton(
            botones, text="Cambiar contraseña", image=self.icono_guardar, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color=COLOR_AZUL_HOVER, hover_color=COLOR_AZUL,
            corner_radius=10, cursor="hand2", height=44, width=200,
            command=self.confirmar
        ).pack(side="right")

    def _campo(self, parent, texto, secreto=False):
        frame = tk.Frame(parent, bg=COLOR_FONDO)
        tk.Label(
            frame, text=texto, font=("Segoe UI", 10, "bold"),
            bg=COLOR_FONDO, fg=COLOR_TEXTO
        ).pack(anchor="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            frame, height=42, fg_color="#FFFFFF",
            border_color="#64748B", border_width=2,
            text_color="#0F172A", corner_radius=8,
            show="•" if secreto else ""
        )
        entry.pack(fill="x")
        return frame, entry

    def _validar_cedula(self, event=None):
        valor = self.entry_cedula.get()
        numeros = "".join(c for c in valor if c.isdigit())[:8]
        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, f"V-{numeros}")

    def confirmar(self):
        usuario = self.entry_usuario.get().strip()
        cedula = self.entry_cedula.get().strip()
        nueva = self.entry_nueva.get()
        confirmar = self.entry_confirmar.get()

        if not usuario or not cedula or cedula == "V-":
            self.label_error.configure(text="Usuario y cédula son obligatorios.")
            return

        if not nueva or not confirmar:
            self.label_error.configure(text="Debes escribir y confirmar la nueva contraseña.")
            return

        if nueva != confirmar:
            self.label_error.configure(text="Las contraseñas no coinciden.")
            return

        resultado = cambiar_contrasena_por_cedula(usuario, cedula, nueva)

        if resultado["ok"]:
            mostrar_exito(self, "Contraseña actualizada", resultado["mensaje"])
            self.cerrar_ventana()
        else:
            self.label_error.configure(text=resultado["mensaje"])