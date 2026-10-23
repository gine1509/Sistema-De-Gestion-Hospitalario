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
from ui.sesion import es_admin
from services.personal_direccion_service import obtener_personal_direccion, DIAS_SEMANA


class VentanaPerfilPersonalDireccion(ctk.CTkToplevel):

    def __init__(self, vista, persona):
        super().__init__(vista)

        self.vista = vista
        self.persona = persona

        self.title("Perfil del Personal")
        self.geometry("620x680")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)

        self.after(10, self._centrar)

        self.transient(vista)
        self.grab_set()

        self._cargar_iconos()
        self._crear_interfaz()

    # ==========================================================
    # CENTRAR
    # ==========================================================

    def _centrar(self):
        if not self.winfo_exists():
            return

        self.update_idletasks()

        ancho = self.winfo_width()
        alto = self.winfo_height()

        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)

        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ==========================================================
    # UTILIDADES
    # ==========================================================

    def _valor(self, clave, defecto="No registrado"):
        valor = self.persona.get(clave)

        if valor is None:
            return defecto

        if isinstance(valor, str):
            valor = valor.strip()
            if not valor:
                return defecto

        return str(valor)

    def _dias_horario(self):
        horarios = self.persona.get("horarios") or []
        if not horarios:
            return "Sin horario asignado"

        dias = sorted({h["dia"] for h in horarios})
        return ", ".join(DIAS_SEMANA.get(d, "") for d in dias)

    def _cargar_iconos(self):
        self.icono_personal = obtener_icono("informacion_personal", 20)
        self.icono_horario = obtener_icono("horario", 20)
        self.icono_horario_perfil = obtener_icono("calendario", 20)
        self.icono_direccion = obtener_icono("direccion", 28)
        self.icono_editar = obtener_icono("editar", 18)
        self.icono_eliminar = obtener_icono("eliminar", 18)

    # ==========================================================
    # INTERFAZ
    # ==========================================================

    def _crear_interfaz(self):

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

        header = tk.Frame(self, bg=COLOR_AZUL, height=100)
        header.pack(fill="x")
        header.pack_propagate(False)

        fila_nombre = tk.Frame(header, bg=COLOR_AZUL)
        fila_nombre.pack(anchor="w", padx=25, pady=(14, 0))

        if self.icono_direccion:
            tk.Label(fila_nombre, image=self.icono_direccion, bg=COLOR_AZUL).pack(side="left", padx=(0, 8))

        tk.Label(
            fila_nombre, text=self._valor("nombre", "Sin nombre"),
            font=("Segoe UI", 17, "bold"), fg="white", bg=COLOR_AZUL
        ).pack(side="left")

        tk.Label(
            header, text=self._valor("cargo", "Personal de dirección"),
            font=("Segoe UI", 12, "bold"), fg="#DCE8FF", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25)

        tk.Label(
            header, text=f"C.I. {self._valor('cedula', 'No registrada')}",
            font=("Segoe UI", 12, "bold"), fg="#DCE8FF", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25, pady=(2, 0))

        activo = bool(self.persona.get("activo"))
        estado_texto = "ACTIVO" if activo else "INACTIVO"
        estado_color = COLOR_VERDE if activo else COLOR_ROJO

        tk.Label(
            header, text=estado_texto, font=("Segoe UI", 9, "bold"),
            fg="white", bg=estado_color, padx=10, pady=4
        ).place(relx=1, x=-20, y=18, anchor="ne")

        # ------------------------------------------------------
        # CONTENIDO
        # ------------------------------------------------------

        contenedor = ctk.CTkScrollableFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=15, pady=15)

        self._crear_seccion(
            contenedor, "Información personal", self.icono_personal,
            [
                ("Cédula", self._valor("cedula", "No registrada")),
                ("Nombres", self._valor("nombres")),
                ("Apellidos", self._valor("apellidos")),
                ("Teléfono", self._valor("telefono")),
                ("Correo", self._valor("correo")),
                ("Cargo", self._valor("cargo")),
            ]
        )

        self._crear_seccion(
            contenedor, "Información laboral", self.icono_personal,
            [
                ("Fecha de ingreso", self._valor("fecha_ingreso")),
                ("Observación", self._valor("observacion")),
            ]
        )

        self._crear_seccion(
            contenedor, "Horario asignado", self.icono_horario_perfil,
            [
                ("Días asignados", self._dias_horario()),
            ]
        )

        datos_estado = [("Estatus", estado_texto)]

        if not activo:
            datos_estado.extend([
                ("Causa de inactividad", self._valor("causa_inactividad")),
                ("Fecha inicio de inactividad", self._valor("fecha_inicio_inactividad")),
                ("Fecha fin de inactividad", self._valor("fecha_fin_inactividad")),
                ("Tiempo de inactividad", self._valor("tiempo_inactividad")),
            ])

        self._crear_seccion(contenedor, "Estado", self.icono_personal, datos_estado)

        # ------------------------------------------------------
        # BOTONES FIJOS
        # ------------------------------------------------------

        botones = tk.Frame(self, bg=COLOR_FONDO)
        botones.pack(fill="x", padx=15, pady=(0, 15))

        # Eliminar personal de dirección: acción exclusiva del administrador.
        if es_admin():
            btn_eliminar = ctk.CTkButton(
                botones, text="Eliminar", image=self.icono_eliminar, compound="left",
                font=("Segoe UI", 13, "bold"), text_color="white",
                fg_color=COLOR_ROJO, hover_color="#B91C1C",
                corner_radius=10, cursor="hand2", height=42, width=150,
                command=self._eliminar
            )
            btn_eliminar.pack(side="left")

        btn_editar = ctk.CTkButton(
            botones, text="Editar", image=self.icono_editar, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color=COLOR_AZUL_HOVER, hover_color=COLOR_AZUL,
            corner_radius=10, cursor="hand2", height=42, width=150,
            command=self._editar
        )
        btn_editar.pack(side="right")

        btn_horario = ctk.CTkButton(
            botones, text="Horario", image=self.icono_horario, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color="#475569", hover_color="#334155",
            corner_radius=10, cursor="hand2", height=42, width=150,
            command=self._horario
        )
        btn_horario.pack(side="right", padx=(0, 10))

    # ==========================================================
    # SECCIONES
    # ==========================================================

    def _crear_seccion(self, parent, titulo, icono, datos):
        tarjeta = tk.Frame(parent, bg=COLOR_BLANCO, highlightbackground=COLOR_BORDE, highlightthickness=1)
        tarjeta.pack(fill="x", pady=(0, 12))

        encabezado = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        encabezado.pack(fill="x", padx=15, pady=(15, 10))

        if icono:
            tk.Label(encabezado, image=icono, bg=COLOR_BLANCO).pack(side="left")

        tk.Label(
            encabezado, text=titulo, font=("Segoe UI", 12, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_BLANCO
        ).pack(side="left", padx=(8, 0))

        separador = tk.Frame(tarjeta, bg="#EEF2F7", height=1)
        separador.pack(fill="x", padx=15)

        contenido = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        contenido.pack(fill="x", padx=15, pady=10)

        contenido.grid_columnconfigure(0, weight=1, uniform="columna")
        contenido.grid_columnconfigure(1, weight=1, uniform="columna")

        fila_grid = 0
        for i in range(0, len(datos), 2):
            izquierda = tk.Frame(contenido, bg=COLOR_BLANCO)
            izquierda.grid(row=fila_grid, column=0, sticky="nw", pady=6, padx=(0, 10))

            etiqueta1, valor1 = datos[i]
            tk.Label(
                izquierda, text=f"{etiqueta1}:", font=("Segoe UI", 10, "bold"),
                fg=COLOR_TEXTO, bg=COLOR_BLANCO
            ).pack(anchor="w")

            tk.Label(
                izquierda, text=valor1 if valor1 else "No registrado", font=("Segoe UI", 10),
                fg=COLOR_SECUNDARIO, bg=COLOR_BLANCO, wraplength=250, justify="left"
            ).pack(anchor="w")

            if i + 1 < len(datos):
                derecha = tk.Frame(contenido, bg=COLOR_BLANCO)
                derecha.grid(row=fila_grid, column=1, sticky="nw", pady=6, padx=(10, 0))

                etiqueta2, valor2 = datos[i + 1]
                tk.Label(
                    derecha, text=f"{etiqueta2}:", font=("Segoe UI", 10, "bold"),
                    fg=COLOR_TEXTO, bg=COLOR_BLANCO
                ).pack(anchor="w")

                tk.Label(
                    derecha, text=valor2 if valor2 else "No registrado", font=("Segoe UI", 10),
                    fg=COLOR_SECUNDARIO, bg=COLOR_BLANCO, wraplength=250, justify="left"
                ).pack(anchor="w")

            fila_grid += 1

    # ==========================================================
    # ACCIONES
    # ==========================================================

    def _editar(self):
        self.destroy()
        self.vista.editar(self.persona)

    def _eliminar(self):
        self.destroy()
        self.vista.eliminar(self.persona)

    def _horario(self):
        self.destroy()
        self.vista.abrir_asignar_horario(self.persona)
