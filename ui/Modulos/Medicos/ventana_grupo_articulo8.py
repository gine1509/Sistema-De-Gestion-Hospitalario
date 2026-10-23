import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import calendar
from datetime import date, datetime

from .colores import (
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_BORDE,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
)

from services.guardia_service import (
    listar_grupos_articulo8,
    obtener_miembros_grupo_articulo8,
    obtener_mapa_grupos_medicos,
    obtener_horario_grupo_articulo8,
    crear_grupo_articulo8,
    actualizar_miembros_grupo_articulo8,
    guardar_horario_grupo_articulo8,
    eliminar_grupo_articulo8,
)
from ui.mensajes import mostrar_exito, mostrar_error


# ================================================================
# VENTANA DE GRUPOS ARTÍCULO 8 (+ MÉDICOS INTERNOS)
# ================================================================
# Administra de punta a punta un grupo: nombre, integrantes
# (Artículo 8 e Internos) y el horario de guardias que comparten.
# Un médico (de cualquier tipo) no puede pertenecer a más de un grupo.

class VentanaGrupoArticulo8(ctk.CTkToplevel):

    ANCHO = 850
    ALTO = 680

    def __init__(
        self,
        parent,
        id_grupo_actual=None,
        id_medico_actual=None,
        al_guardar=None
    ):
        super().__init__(parent)

        self.parent = parent
        self.id_grupo_actual = id_grupo_actual
        self.id_medico_actual = id_medico_actual
        self.al_guardar = al_guardar

        self.title("Grupos Artículo 8")
        self.geometry(f"{self.ANCHO}x{self.ALTO}")
        self.resizable(False, False)
        self.configure(fg_color="#F4F7FB")
        self.transient(parent)
        self.grab_set()

        hoy = date.today()
        self.mes_actual = hoy.month
        self.anio_actual = hoy.year
        self.fechas_horario = set()
        self.botones_dias = {}
        self.chk_vars = {}

        self._cargar_datos()
        self._crear_interfaz()
        self._cargar_grupo_actual()

        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.ANCHO) // 2
        y = (self.winfo_screenheight() - self.ALTO) // 2
        self.geometry(f"{self.ANCHO}x{self.ALTO}+{x}+{y}")

    # ============================================================
    # DATOS
    # ============================================================

    def _cargar_datos(self):
        self.medicos_articulo8, self.medicos_internos = self._listar_elegibles()
        self.grupos = listar_grupos_articulo8()
        self.mapa_grupos_medicos = obtener_mapa_grupos_medicos()

    def _listar_elegibles(self):
        """Devuelve (lista_articulo8, lista_internos)."""
        from services.medico_service import listar_medicos
        medicos = listar_medicos()

        articulo8 = []
        internos = []

        for m in medicos:
            cargo = (m.get("cargo") or "").strip().upper()
            # Normalizar acentos simples
            cargo_norm = (
                cargo
                .replace("Á", "A").replace("É", "E")
                .replace("Í", "I").replace("Ó", "O")
                .replace("Ú", "U")
            )

            if cargo_norm == "ARTICULO 8":
                articulo8.append(m)
            elif "INTERNO" in cargo_norm:  # MEDICO INTERNO, MÉDICO INTERNO, etc.
                internos.append(m)

        return articulo8, internos

    # ============================================================
    # INTERFAZ
    # ============================================================

    def _crear_interfaz(self):
        tk.Label(
            self,
            text="Grupos de Artículo 8",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_TEXTO,
            bg="#F4F7FB"
        ).pack(anchor="w", padx=25, pady=(20, 3))

        tk.Label(
            self,
            text=(
                "Un grupo comparte un único horario de guardias: todos sus "
                "integrantes (Artículo 8 e Internos) reciben las mismas fechas. "
                "Ningún médico puede pertenecer a más de un grupo."
            ),
            font=("Segoe UI", 9),
            fg=COLOR_SECUNDARIO,
            bg="#F4F7FB",
            wraplength=780,
            justify="left"
        ).pack(anchor="w", padx=25, pady=(0, 12))

        # --------------------------------------------------------
        # SELECTOR DE GRUPO
        # --------------------------------------------------------
        fila_grupo = tk.Frame(self, bg="#F4F7FB")
        fila_grupo.pack(fill="x", padx=25, pady=(0, 10))

        tk.Label(
            fila_grupo,
            text="Grupo",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_TEXTO,
            bg="#F4F7FB"
        ).pack(side="left")

        self.grupo_var = tk.StringVar(value="Nuevo grupo")
        self.combo_grupo = ttk.Combobox(
            fila_grupo,
            textvariable=self.grupo_var,
            values=["Nuevo grupo"] + [g["nombre"] for g in self.grupos],
            state="readonly",
            width=28,
            font=("Segoe UI", 10)
        )
        self.combo_grupo.pack(side="left", padx=(10, 8), ipady=4)
        self.combo_grupo.bind("<<ComboboxSelected>>", self._cambio_grupo)

        tk.Button(
            fila_grupo,
            text="+ Crear grupo",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_AZUL,
            bg="#F4F7FB",
            activebackground="#E8F0FA",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._nuevo_grupo
        ).pack(side="left", padx=(6, 0))

        # --------------------------------------------------------
        # NOMBRE
        # --------------------------------------------------------
        tk.Label(
            self,
            text="Nombre del grupo",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_TEXTO,
            bg="#F4F7FB"
        ).pack(anchor="w", padx=25)

        self.entry_nombre = tk.Entry(
            self,
            font=("Segoe UI", 10),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            relief="solid",
            bd=1
        )
        self.entry_nombre.pack(fill="x", padx=25, pady=(5, 12), ipady=7)

        # --------------------------------------------------------
        # BOTONES (fijos abajo)
        # --------------------------------------------------------
        botones = tk.Frame(self, bg="#F4F7FB")
        botones.pack(side="bottom", fill="x", padx=25, pady=(0, 20))

        tk.Button(
            botones,
            text="Cancelar",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg="#E2E8F0",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right")

        tk.Button(
            botones,
            text="Guardar grupo",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg=COLOR_AZUL,
            activebackground=COLOR_AZUL_HOVER,
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._guardar
        ).pack(side="right", padx=(0, 10))

        self.btn_eliminar = tk.Button(
            botones,
            text="Eliminar grupo",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg="#DC2626",
            activebackground="#B91C1C",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._eliminar_grupo,
            state="disabled"
        )
        self.btn_eliminar.pack(side="left")
        
        

        self.btn_exportar = tk.Button(
            botones,
            text="Exportar PDF",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg="#DC2626",
            activebackground="#B91C1C",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._exportar_pdf,
            state="normal"          # siempre disponible
        )
        self.btn_exportar.pack(side="left", padx=(10, 0))

        # --------------------------------------------------------
        # CUERPO: INTEGRANTES + HORARIO
        # --------------------------------------------------------
        cuerpo = tk.Frame(self, bg="#F4F7FB")
        cuerpo.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        panel_integrantes = tk.Frame(
            cuerpo,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        panel_integrantes.pack(side="left", fill="both", expand=True, padx=(0, 8))

        panel_horario = tk.Frame(
            cuerpo,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        panel_horario.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self._crear_panel_integrantes(panel_integrantes)
        self._crear_panel_horario(panel_horario)

    # ------------------------------------------------------------
    # PANEL: INTEGRANTES (Artículo 8 + Internos)
    # ------------------------------------------------------------

    def _crear_panel_integrantes(self, contenedor):
        tk.Label(
            contenedor,
            text="Integrantes",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(anchor="w", padx=12, pady=(12, 4))

        marco = tk.Frame(contenedor, bg=COLOR_BLANCO)
        marco.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        canvas = tk.Canvas(
            marco,
            bg=COLOR_BLANCO,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.frame_integrantes = tk.Frame(canvas, bg=COLOR_BLANCO)
        ventana_canvas = canvas.create_window(
            (0, 0),
            window=self.frame_integrantes,
            anchor="nw"
        )

        self.frame_integrantes.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(ventana_canvas, width=e.width)
        )

        self.chk_vars = {}

        hay_alguno = bool(self.medicos_articulo8 or self.medicos_internos)

        if not hay_alguno:
            tk.Label(
                self.frame_integrantes,
                text="No hay médicos Artículo 8 ni Internos registrados.",
                font=("Segoe UI", 9),
                fg=COLOR_SECUNDARIO,
                bg=COLOR_BLANCO
            ).pack(anchor="w", pady=6)
            return

        # ---- Sección Artículo 8 ----
        self._agregar_seccion_medicos(
            "Artículo 8",
            self.medicos_articulo8
        )

        # ---- Sección Internos ----
        self._agregar_seccion_medicos(
            "Médicos Internos",
            self.medicos_internos
        )

    def _agregar_seccion_medicos(self, titulo, lista_medicos):
        """Crea un encabezado de sección y los checkbuttons correspondientes."""
        if not lista_medicos:
            return

        # Separador / título de sección
        frame_titulo = tk.Frame(self.frame_integrantes, bg=COLOR_BLANCO)
        frame_titulo.pack(fill="x", pady=(10, 4))

        tk.Label(
            frame_titulo,
            text=titulo,
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_AZUL,
            bg=COLOR_BLANCO
        ).pack(side="left")

        tk.Frame(
            frame_titulo,
            bg=COLOR_BORDE,
            height=1
        ).pack(side="left", fill="x", expand=True, padx=(8, 0), pady=6)

        for medico in lista_medicos:
            id_medico = medico["id_medico"]
            otro_grupo = self.mapa_grupos_medicos.get(id_medico)

            texto = f"{medico['nombre']}  •  {medico['cedula']}"
            if otro_grupo:
                texto += f"  —  {otro_grupo['nombre']}"

            var = tk.BooleanVar(value=False)

            chk = tk.Checkbutton(
                self.frame_integrantes,
                text=texto,
                variable=var,
                font=("Segoe UI", 10),
                fg=COLOR_TEXTO,
                bg=COLOR_BLANCO,
                activebackground=COLOR_BLANCO,
                disabledforeground="#B0B8C4",
                selectcolor=COLOR_BLANCO,
                anchor="w",
                justify="left"
            )
            chk.pack(fill="x", pady=1)

            self.chk_vars[id_medico] = {
                "var": var,
                "widget": chk,
                "otro_grupo": otro_grupo["id_grupo"] if otro_grupo else None,
            }

    def _actualizar_estado_integrantes(self):
        """Bloquea los médicos que ya pertenecen a otro grupo distinto
        del que se está editando."""
        grupo_editado = self._id_grupo_seleccionado()

        for id_medico, info in self.chk_vars.items():
            if info["otro_grupo"] and info["otro_grupo"] != grupo_editado:
                info["widget"].configure(state="disabled")
                info["var"].set(False)
            else:
                info["widget"].configure(state="normal")

    def _id_grupo_seleccionado(self):
        nombre = self.grupo_var.get()
        if nombre == "Nuevo grupo":
            return None
        grupo = next(
            (g for g in self.grupos if g["nombre"] == nombre),
            None
        )
        return grupo["id_grupo"] if grupo else None

    # ------------------------------------------------------------
    # PANEL: HORARIO
    # ------------------------------------------------------------

    def _crear_panel_horario(self, contenedor):
        tk.Label(
            contenedor,
            text="Horario del grupo",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(anchor="w", padx=12, pady=(12, 6))

        nav = tk.Frame(contenedor, bg=COLOR_BLANCO)
        nav.pack(fill="x", padx=12)

        tk.Button(
            nav,
            text="‹",
            font=("Segoe UI", 15),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            activebackground="#E8F0FA",
            relief="flat",
            bd=0,
            width=2,
            cursor="hand2",
            command=self._mes_anterior
        ).pack(side="left")

        self.label_mes = tk.Label(
            nav,
            text="",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        )
        self.label_mes.pack(side="left", expand=True)

        tk.Button(
            nav,
            text="›",
            font=("Segoe UI", 15),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            activebackground="#E8F0FA",
            relief="flat",
            bd=0,
            width=2,
            cursor="hand2",
            command=self._mes_siguiente
        ).pack(side="right")

        self.calendario = tk.Frame(contenedor, bg=COLOR_BLANCO)
        self.calendario.pack(fill="both", expand=True, padx=12, pady=(6, 6))

        self.label_seleccion = tk.Label(
            contenedor,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO
        )
        self.label_seleccion.pack(anchor="e", padx=12, pady=(0, 12))

        self._crear_calendario()

    def _crear_calendario(self):
        for widget in self.calendario.winfo_children():
            widget.destroy()

        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
            "Diciembre"
        ]
        self.label_mes.configure(
            text=f"{meses[self.mes_actual - 1]} {self.anio_actual}"
        )

        dias_semana = ["L", "M", "X", "J", "V", "S", "D"]
        for columna, nombre in enumerate(dias_semana):
            self.calendario.grid_columnconfigure(columna, weight=1)
            tk.Label(
                self.calendario,
                text=nombre,
                font=("Segoe UI", 8, "bold"),
                fg=COLOR_BLANCO,
                bg=COLOR_AZUL,
                pady=4
            ).grid(row=0, column=columna, sticky="nsew", padx=1, pady=1)

        cal = calendar.Calendar(firstweekday=0)
        semanas = cal.monthdayscalendar(self.anio_actual, self.mes_actual)
        self.botones_dias = {}

        for fila, semana in enumerate(semanas, start=1):
            self.calendario.grid_rowconfigure(fila, weight=1)

            for columna, numero in enumerate(semana):
                if numero == 0:
                    tk.Frame(
                        self.calendario,
                        bg="#F8FAFC"
                    ).grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)
                    continue

                fecha = date(self.anio_actual, self.mes_actual, numero)
                seleccionado = fecha in self.fechas_horario
                hoy = fecha == date.today()

                if seleccionado:
                    bg, fg, active_bg = COLOR_AZUL, "white", COLOR_AZUL_HOVER
                else:
                    bg, fg, active_bg = "#FFFFFF", COLOR_TEXTO, "#EFF6FF"

                boton = tk.Button(
                    self.calendario,
                    text=str(numero),
                    font=("Segoe UI", 8, "bold" if seleccionado or hoy else "normal"),
                    fg=fg,
                    bg=bg,
                    activeforeground=fg,
                    activebackground=active_bg,
                    relief="solid" if hoy else "flat",
                    bd=1 if hoy else 0,
                    highlightthickness=0,
                    cursor="hand2",
                    command=lambda f=fecha: self._alternar_fecha(f)
                )
                boton.grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)
                self.botones_dias[fecha] = boton

    def _alternar_fecha(self, fecha):
        if fecha in self.fechas_horario:
            self.fechas_horario.remove(fecha)
        else:
            self.fechas_horario.add(fecha)
        self._crear_calendario()

    def _mes_anterior(self):
        self.mes_actual -= 1
        if self.mes_actual < 1:
            self.mes_actual = 12
            self.anio_actual -= 1
        self._crear_calendario()

    def _mes_siguiente(self):
        self.mes_actual += 1
        if self.mes_actual > 12:
            self.mes_actual = 1
            self.anio_actual += 1
        self._crear_calendario()

    # ============================================================
    # CARGA / CAMBIO DE GRUPO
    # ============================================================

    def _nuevo_grupo(self):
        self.grupo_var.set("Nuevo grupo")
        self._cambio_grupo()

    def _cargar_grupo_actual(self):
        if not self.id_grupo_actual:
            self._actualizar_estado_integrantes()
            return

        grupo = next(
            (g for g in self.grupos if g["id_grupo"] == self.id_grupo_actual),
            None
        )
        if not grupo:
            self._actualizar_estado_integrantes()
            return

        self.grupo_var.set(grupo["nombre"])
        self._cambio_grupo()

    def _cambio_grupo(self, event=None):
        nombre = self.grupo_var.get()

        if nombre == "Nuevo grupo":
            self.entry_nombre.configure(state="normal")
            self.entry_nombre.delete(0, "end")

            for info in self.chk_vars.values():
                info["var"].set(False)

            self.fechas_horario = set()
            self._actualizar_estado_integrantes()
            self._crear_calendario()
            self.btn_eliminar.configure(state="disabled")
            # Sin grupo → el botón sigue activo para poder exportar TODOS
            self.btn_exportar.configure(state="normal")
            return

        grupo = next(
            (g for g in self.grupos if g["nombre"] == nombre),
            None
        )
        if not grupo:
            return

        self.entry_nombre.configure(state="normal")
        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, grupo["nombre"])
        self.entry_nombre.configure(state="disabled")

        miembros = {
            m["id_medico"]
            for m in obtener_miembros_grupo_articulo8(grupo["id_grupo"])
        }

        for id_medico, info in self.chk_vars.items():
            info["var"].set(id_medico in miembros)

        self.fechas_horario = set(
            obtener_horario_grupo_articulo8(grupo["id_grupo"])
        )

        self._actualizar_estado_integrantes()
        self._crear_calendario()
        self.btn_eliminar.configure(state="normal")
        self.btn_exportar.configure(state="normal")

    # ============================================================
    # GUARDAR
    # ============================================================

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()

        ids_medicos = [
            id_medico
            for id_medico, info in self.chk_vars.items()
            if info["var"].get()
        ]

        if not nombre:
            mostrar_error(self, "Grupo incompleto", "Indique el nombre del grupo.")
            return

        if not ids_medicos:
            mostrar_error(
                self,
                "Grupo incompleto",
                "Seleccione al menos un médico (Artículo 8 o Interno)."
            )
            return

        seleccionado = self.grupo_var.get()

        if seleccionado == "Nuevo grupo":
            resultado = crear_grupo_articulo8(nombre, ids_medicos)
        else:
            grupo = next(
                (g for g in self.grupos if g["nombre"] == seleccionado),
                None
            )
            if not grupo:
                mostrar_error(self, "Grupo", "No se encontró el grupo seleccionado.")
                return

            resultado = actualizar_miembros_grupo_articulo8(
                grupo["id_grupo"],
                ids_medicos
            )
            resultado["id_grupo"] = grupo["id_grupo"]

        if not resultado.get("ok"):
            mostrar_error(
                self,
                "No se pudo guardar",
                resultado.get("mensaje", "Ocurrió un error.")
            )
            return

        id_grupo = resultado.get("id_grupo")
        if not id_grupo:
            grupos_actualizados = listar_grupos_articulo8()
            grupo_creado = next(
                (g for g in grupos_actualizados if g["nombre"] == nombre.upper()),
                None
            )
            id_grupo = grupo_creado["id_grupo"] if grupo_creado else None

        if id_grupo:
            resultado_horario = guardar_horario_grupo_articulo8(
                id_grupo,
                sorted(self.fechas_horario)
            )
            if not resultado_horario.get("ok"):
                mostrar_error(
                    self,
                    "Grupo guardado, horario pendiente",
                    resultado_horario.get(
                        "mensaje",
                        "El grupo se guardó, pero no se pudo guardar el horario."
                    )
                )
                if self.al_guardar:
                    self.al_guardar()
                self.destroy()
                return

        mostrar_exito(
            self,
            "Grupo guardado",
            "El grupo y su horario de guardias se guardaron correctamente."
        )

        if self.al_guardar:
            self.al_guardar()
        self.destroy()

    def _eliminar_grupo(self):
        nombre = self.grupo_var.get()
        if nombre == "Nuevo grupo":
            return

        grupo = next(
            (g for g in self.grupos if g["nombre"] == nombre),
            None
        )
        if not grupo:
            mostrar_error(self, "Grupo", "No se encontró el grupo seleccionado.")
            return

        from tkinter import messagebox
        confirmar = messagebox.askyesno(
            "Eliminar grupo",
            f"¿Eliminar el grupo «{grupo['nombre']}»?\n\n"
            "Los médicos que pertenecen a él quedarán sin grupo.",
            parent=self
        )
        if not confirmar:
            return

        resultado = eliminar_grupo_articulo8(grupo["id_grupo"])

        if not resultado.get("ok"):
            mostrar_error(
                self,
                "No se pudo eliminar",
                resultado.get("mensaje", "Ocurrió un error.")
            )
            return

        mostrar_exito(
            self,
            "Grupo eliminado",
            resultado.get("mensaje", "El grupo se eliminó correctamente.")
        )

        if self.al_guardar:
            self.al_guardar()
        self.destroy()
    
    def _exportar_pdf(self):
        from services.exportar_grupos_service import (
            exportar_horario_grupo_pdf,
            exportar_todos_los_grupos_pdf,
        )

        nombre = self.grupo_var.get()

        if nombre == "Nuevo grupo":
            # Sin grupo seleccionado → exportar TODOS
            exportar_todos_los_grupos_pdf(
                anio=self.anio_actual,
                mes=self.mes_actual,
                parent_window=self,
            )
            return

        grupo = next((g for g in self.grupos if g["nombre"] == nombre), None)
        if not grupo:
            mostrar_error(self, "Exportar", "No se encontró el grupo seleccionado.")
            return

        # Grupo seleccionado → exportar solo ese
        exportar_horario_grupo_pdf(
            id_grupo=grupo["id_grupo"],
            nombre_grupo=grupo["nombre"],
            anio=self.anio_actual,
            mes=self.mes_actual,
            parent_window=self,
        )