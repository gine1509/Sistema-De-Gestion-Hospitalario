import tkinter as tk
from tkinter import ttk
from datetime import date
import calendar

from ui.iconos import obtener_icono
from services.guardia_service import (
    obtener_guardias_mes,
    listar_grupos_articulo8,
    obtener_miembros_grupo_articulo8,
    obtener_horario_grupo_articulo8,
)

from services.medico_service import (
    listar_cargos,
    listar_centros,
    listar_medicos
)
from services.exportar_guardias_service import mostrar_dialogo_exportar_guardias
from services.exportar_guardias_mes_service import mostrar_dialogo_exportar_guardias_mes
from services.exportar_grupos_service import (
    exportar_todos_los_grupos_pdf,
    exportar_horario_grupo_pdf,
)


# ============================================================
# COLORES
# ============================================================

COLOR_FONDO = "#F4F7FB"
COLOR_BLANCO = "#FFFFFF"

COLOR_TEXTO = "#0F172A"
COLOR_SECUNDARIO = "#64748B"

COLOR_AZUL = "#2563EB"
COLOR_AZUL_HOVER = "#0B4F94"

COLOR_BORDE = "#D5DEE8"

COLOR_DIA = "#FFFFFF"
COLOR_DIA_HOY = "#EFF6FF"

COLOR_HEADER_CALENDARIO = "#2563EB"


# ============================================================
# VISTA GUARDIAS
# ============================================================

class VistaGuardias(tk.Frame):

    def __init__(self, parent):

        super().__init__(
            parent,
            bg=COLOR_FONDO
        )

        # ----------------------------------------------------
        # FECHA ACTUAL DEL CALENDARIO
        # ----------------------------------------------------

        hoy = date.today()

        self.mes_actual = hoy.month
        self.anio_actual = hoy.year

        # ----------------------------------------------------
        # VARIABLES DE FILTROS
        # ----------------------------------------------------

        self.busqueda_var = tk.StringVar()

        self.cargo_var = tk.StringVar(
            value="Todos los cargos"
        )

        self.especialidad_var = tk.StringVar(
            value="Todas las especialidades"
        )

        self.centro_var = tk.StringVar(
            value="HOSPITAL PADRE JUSTO"
        )
        self.guardias_mes = {}

        # ----------------------------------------------------
        # ICONOS
        # ----------------------------------------------------

        self.icon_buscar = obtener_icono(
            "buscar",
            18
        )

        self.icon_exportar = obtener_icono(
            "exportar",
            18
        )

        # ----------------------------------------------------
        # INTERFAZ
        # ----------------------------------------------------

        self.crear_interfaz()

    # ========================================================
    # INTERFAZ PRINCIPAL
    # ========================================================

    def crear_interfaz(self):

        # ----------------------------------------------------
        # SCROLL PRINCIPAL
        # ----------------------------------------------------

        self.canvas = tk.Canvas(
            self,
            bg=COLOR_FONDO,
            highlightthickness=0
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.contenido_scroll = tk.Frame(
            self.canvas,
            bg=COLOR_FONDO
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.contenido_scroll,
            anchor="nw"
        )

        self.contenido_scroll.bind(
            "<Configure>",
            self.actualizar_scroll
        )

        self.canvas.bind(
            "<Configure>",
            self.ajustar_ancho
        )

        # ----------------------------------------------------
        # SCROLL CON RUEDA DEL MOUSE
        # ----------------------------------------------------

        self.canvas.bind_all(
            "<MouseWheel>",
            self._scroll_mouse
        )

        # ----------------------------------------------------
        # CONTENEDOR
        # ----------------------------------------------------

        contenido = tk.Frame(
            self.contenido_scroll,
            bg=COLOR_FONDO
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=25
        )

        # ----------------------------------------------------
        # ENCABEZADO
        # ----------------------------------------------------

        self.crear_encabezado(
            contenido
        )

        # ----------------------------------------------------
        # FILTROS
        # ----------------------------------------------------

        self.crear_filtros(
            contenido
        )

        # ----------------------------------------------------
        # NAVEGACIÓN DEL MES
        # ----------------------------------------------------

        self.crear_navegacion_mes(
            contenido
        )

        # ----------------------------------------------------
        # CALENDARIO
        # ----------------------------------------------------

        self.contenedor_calendario = tk.Frame(
            contenido,
            bg=COLOR_FONDO
        )

        self.contenedor_calendario.pack(
            fill="both",
            expand=True,
            pady=(10, 0)
        )

        self.crear_calendario()

    # ========================================================
    # ENCABEZADO
    # ========================================================

    def crear_encabezado(self, parent):

        encabezado = tk.Frame(
            parent,
            bg=COLOR_FONDO
        )

        encabezado.pack(
            fill="x",
            pady=(0, 20)
        )

        # ----------------------------------------------------
        # CONTENEDOR DE TEXTOS (IZQUIERDA)
        # ----------------------------------------------------
        
        frame_textos = tk.Frame(
            encabezado,
            bg=COLOR_FONDO
        )
        
        frame_textos.pack(
            side="left"
        )

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        tk.Label(
            frame_textos,
            text="Guardias",
            font=(
                "Segoe UI",
                24,
                "bold"
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO
        ).pack(
            anchor="w"
        )
        
        # ----------------------------------------------------
        # DESCRIPCIÓN
        # ----------------------------------------------------

        tk.Label(
            frame_textos,
            text="Consulta y visualiza las guardias del personal médico.",
            font=(
                "Segoe UI",
                10
            ),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_FONDO
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        # ----------------------------------------------------
        # BOTÓN EXPORTAR
        # ----------------------------------------------------

        self.boton_exportar = tk.Button(
            encabezado,
            text="Exportar",
            image=self.icon_exportar,
            compound="left",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg=COLOR_AZUL,
            fg="white",
            activebackground=COLOR_AZUL_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=9,
            cursor="hand2",
            command=self.exportar
        )

        self.boton_exportar.pack(
            side="right"
        )

        self.boton_exportar.bind(
            "<Enter>",
            lambda e: self.boton_exportar.config(
                bg=COLOR_AZUL_HOVER
            )
        )

        self.boton_exportar.bind(
            "<Leave>",
            lambda e: self.boton_exportar.config(
                bg=COLOR_AZUL
            )
        )

    # ========================================================
    # FILTROS
    # ========================================================

    def crear_filtros(self, parent):
        
        # --- Obtener datos de la BD ---
        cargos_bd = listar_cargos()
        centros_bd = listar_centros()

        # Obtener médicos para sacar las especialidades
        medicos_bd = listar_medicos()

        especialidades_bd = sorted({
            str(medico.get("especialidad")).strip()
            for medico in medicos_bd
            if medico.get("especialidad")
            and str(medico.get("especialidad")).strip()
        })

        # Opción especial para ver los grupos de Artículo 8
        lista_cargos = [
            "Todos los cargos",
            "Guardias médicas"          # ← NUEVA OPCIÓN
        ] + cargos_bd

        lista_especialidades = [
            "Todas las especialidades"
        ] + especialidades_bd

        lista_centros = [
            "Todos los centros"
        ] + centros_bd
        
        # Por seguridad, si el hospital no viene en la BD aún, lo agregamos
        if "HOSPITAL PADRE JUSTO" not in lista_centros:
            lista_centros.append("HOSPITAL PADRE JUSTO")

        contenedor = tk.Frame(
            parent,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        contenedor.pack(
            fill="x",
            pady=(0, 20)
        )

        interior = tk.Frame(
            contenedor,
            bg=COLOR_BLANCO
        )

        interior.pack(
            fill="x",
            padx=18,
            pady=16
        )

        # ----------------------------------------------------
        # BUSCADOR
        # ----------------------------------------------------

        bloque_busqueda = tk.Frame(
            interior,
            bg=COLOR_BLANCO
        )

        bloque_busqueda.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 12)
        )

        tk.Label(
            bloque_busqueda,
            text="Buscar médico",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        buscador_frame = tk.Frame(
            bloque_busqueda,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        buscador_frame.pack(
            fill="x"
        )

        if self.icon_buscar:

            tk.Label(
                buscador_frame,
                image=self.icon_buscar,
                bg=COLOR_BLANCO
            ).pack(
                side="left",
                padx=(10, 5)
            )

        self.entry_busqueda = tk.Entry(
            buscador_frame,
            textvariable=self.busqueda_var,
            font=(
                "Segoe UI",
                11
            ),
            relief="flat",
            bd=0,
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        )

        self.entry_busqueda.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7,
            padx=(0, 10)
        )

        self.entry_busqueda.bind(
            "<KeyRelease>",
            lambda e: self.aplicar_filtros()
        )

        # ----------------------------------------------------
        # CARGO (único)
        # ----------------------------------------------------

        bloque_cargo = tk.Frame(
            interior,
            bg=COLOR_BLANCO
        )

        bloque_cargo.pack(
            side="left",
            padx=8
        )

        tk.Label(
            bloque_cargo,
            text="Cargo",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        self.combo_cargo = ttk.Combobox(
            bloque_cargo,
            textvariable=self.cargo_var,
            values=lista_cargos,
            state="readonly",
            width=22,
            font=("Segoe UI", 10)
        )

        self.combo_cargo.pack(ipady=5)

        self.combo_cargo.bind(
            "<<ComboboxSelected>>",
            lambda e: self.aplicar_filtros()
        )

        # ----------------------------------------------------
        # ESPECIALIDAD
        # ----------------------------------------------------

        bloque_especialidad = tk.Frame(
            interior,
            bg=COLOR_BLANCO
        )

        bloque_especialidad.pack(
            side="left",
            padx=8
        )

        tk.Label(
            bloque_especialidad,
            text="Especialidad",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        self.combo_especialidad = ttk.Combobox(
            bloque_especialidad,
            textvariable=self.especialidad_var,
            values=lista_especialidades,
            state="readonly",
            width=22,
            font=("Segoe UI", 10)
        )

        self.combo_especialidad.pack(
            ipady=5
        )

        self.combo_especialidad.bind(
            "<<ComboboxSelected>>",
            lambda e: self.aplicar_filtros()
        )

        # ----------------------------------------------------
        # CENTRO
        # ----------------------------------------------------

        bloque_centro = tk.Frame(
            interior,
            bg=COLOR_BLANCO
        )

        bloque_centro.pack(
            side="left",
            padx=(8, 0)
        )

        tk.Label(
            bloque_centro,
            text="Centro",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        self.combo_centro = ttk.Combobox(
            bloque_centro,
            textvariable=self.centro_var,
            values=lista_centros,  
            state="readonly",
            width=22,
            font=("Segoe UI", 10)
        )

        self.combo_centro.pack(
            ipady=5
        )

        self.combo_centro.bind(
            "<<ComboboxSelected>>",
            lambda e: self.aplicar_filtros()
        )

    # ========================================================
    # NAVEGACIÓN DEL MES
    # ========================================================

    def crear_navegacion_mes(self, parent):

        navegacion = tk.Frame(
            parent,
            bg=COLOR_FONDO
        )

        navegacion.pack(
            fill="x",
            pady=(0, 5)
        )

        # ----------------------------------------------------
        # BOTÓN MES ANTERIOR
        # ----------------------------------------------------

        self.boton_anterior = tk.Button(
            navegacion,
            text="‹",
            font=(
                "Segoe UI",
                24
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            activebackground="#E8F0FA",
            activeforeground=COLOR_AZUL,
            relief="flat",
            bd=0,
            width=3,
            cursor="hand2",
            command=self.mes_anterior
        )

        self.boton_anterior.pack(
            side="left"
        )

        # ----------------------------------------------------
        # MES
        # ----------------------------------------------------

        self.label_mes = tk.Label(
            navegacion,
            text="",
            font=(
                "Segoe UI",
                18,
                "bold"
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO
        )

        self.label_mes.pack(
            side="left",
            expand=True
        )

        # ----------------------------------------------------
        # HOY
        # ----------------------------------------------------

        self.boton_hoy = tk.Button(
            navegacion,
            text="Hoy",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            fg=COLOR_AZUL,
            bg=COLOR_BLANCO,
            activebackground="#E8F0FA",
            activeforeground=COLOR_AZUL_HOVER,
            relief="solid",
            bd=1,
            highlightthickness=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.ir_a_hoy
        )

        self.boton_hoy.pack(
            side="right",
            padx=(0, 10)
        )

        # ----------------------------------------------------
        # BOTÓN MES SIGUIENTE
        # ----------------------------------------------------

        self.boton_siguiente = tk.Button(
            navegacion,
            text="›",
            font=(
                "Segoe UI",
                24
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            activebackground="#E8F0FA",
            activeforeground=COLOR_AZUL,
            relief="flat",
            bd=0,
            width=3,
            cursor="hand2",
            command=self.mes_siguiente
        )

        self.boton_siguiente.pack(
            side="right"
        )

    # ========================================================
    # CALENDARIO
    # ========================================================

    def crear_calendario(self):

        # --------------------------------------------------------
        # LIMPIAR CALENDARIO
        # --------------------------------------------------------

        for widget in self.contenedor_calendario.winfo_children():

            widget.destroy()

        # --------------------------------------------------------
        # ACTUALIZAR TÍTULO
        # --------------------------------------------------------

        nombre_mes = self.obtener_nombre_mes(
            self.mes_actual
        )

        self.label_mes.config(
            text=f"{nombre_mes} {self.anio_actual}"
        )

        # --------------------------------------------------------
        # MODO ESPECIAL: GUARDIAS MÉDICAS (grupos Artículo 8)
        # --------------------------------------------------------

        if self.cargo_var.get() == "Guardias médicas":
            self._cargar_guardias_grupos()
        else:
            # ----------------------------------------------------
            # OBTENER GUARDIAS NORMALES
            # ----------------------------------------------------
            try:
                self.guardias_mes = obtener_guardias_mes(
                    self.anio_actual,
                    self.mes_actual,
                    texto_busqueda=self.busqueda_var.get(),
                    cargo=self._cargos_seleccionados(),
                    centro=self.centro_var.get(),
                    especialidad=self.especialidad_var.get()
                )
            except Exception as e:
                print(f"[Guardias] Error cargando guardias: {e}")
                self.guardias_mes = {}

        # --------------------------------------------------------
        # DÍAS DE LA SEMANA
        # --------------------------------------------------------

        dias_semana = [
            "Dom",
            "Lun",
            "Mar",
            "Mié",
            "Jue",
            "Vie",
            "Sáb"
        ]

        for columna, dia in enumerate(
            dias_semana
        ):

            encabezado = tk.Label(
                self.contenedor_calendario,
                text=dia,
                font=(
                    "Segoe UI",
                    10,
                    "bold"
                ),
                fg="white",
                bg=COLOR_HEADER_CALENDARIO,
                pady=9
            )

            encabezado.grid(
                row=0,
                column=columna,
                sticky="nsew",
                padx=1,
                pady=(0, 1)
            )

            self.contenedor_calendario.grid_columnconfigure(
                columna,
                weight=1,
                uniform="calendario"
            )

        # --------------------------------------------------------
        # CALENDARIO DEL MES
        # --------------------------------------------------------

        calendario = calendar.Calendar(
            firstweekday=6
        )

        semanas = calendario.monthdayscalendar(
            self.anio_actual,
            self.mes_actual
        )

        # --------------------------------------------------------
        # CREAR CADA SEMANA
        # --------------------------------------------------------

        for fila, semana in enumerate(
            semanas,
            start=1
        ):

            self.contenedor_calendario.grid_rowconfigure(
                fila,
                weight=1,
                minsize=115
            )

            for columna, numero_dia in enumerate(
                semana
            ):

                if numero_dia == 0:

                    celda = tk.Frame(
                        self.contenedor_calendario,
                        bg="#E9EEF5",
                        highlightbackground=COLOR_BORDE,
                        highlightthickness=1
                    )

                    celda.grid(
                        row=fila,
                        column=columna,
                        sticky="nsew",
                        padx=1,
                        pady=1
                    )

                    continue

                self.crear_celda_dia(
                    fila,
                    columna,
                    numero_dia
                )

    # ========================================================
    # CARGAR DATOS DE GRUPOS (cuando se elige "Guardias médicas")
    # ========================================================

    def _cargar_guardias_grupos(self):
        """
        Construye self.guardias_mes a partir de los grupos de Artículo 8.
        Cada día tendrá la lista de todos los médicos de los grupos
        que tienen guardia ese día.
        """
        from collections import defaultdict

        self.guardias_mes = {}
        dia_medicos = defaultdict(list)

        try:
            grupos = listar_grupos_articulo8()
            texto = (self.busqueda_var.get() or "").strip().lower()

            for grupo in grupos:
                miembros = obtener_miembros_grupo_articulo8(grupo["id_grupo"]) or []
                fechas = obtener_horario_grupo_articulo8(grupo["id_grupo"]) or []

                # Filtrar por búsqueda de nombre si hay texto
                if texto:
                    miembros = [
                        m for m in miembros
                        if texto in (m.get("nombre") or "").lower()
                    ]
                    if not miembros:
                        continue

                nombres = []
                for m in miembros:
                    nombres.append({
                        "nombre": m.get("nombre", "").strip(),
                        "cargo": m.get("cargo", "Artículo 8 / Interno"),
                        "centro": m.get("centro", ""),
                        "telefono": m.get("telefono", ""),
                        "especialidad": m.get("especialidad", ""),
                        "inactivo": m.get("inactivo", False),
                        "causa_inactividad": m.get("causa_inactividad", ""),
                        "id_medico": m.get("id_medico"),
                        "grupo": grupo.get("nombre", ""),
                    })

                for f in fechas:
                    # Solo fechas del mes que estamos viendo
                    if f.year == self.anio_actual and f.month == self.mes_actual:
                        for medico in nombres:
                            # Evitar duplicados
                            if not any(x["nombre"] == medico["nombre"] for x in dia_medicos[f]):
                                dia_medicos[f].append(medico)

            self.guardias_mes = dict(dia_medicos)

        except Exception as e:
            print(f"[Guardias] Error cargando grupos Artículo 8: {e}")
            self.guardias_mes = {}

    # ========================================================
    # CELDA DEL DÍA
    # ========================================================

    def crear_celda_dia(
        self,
        fila,
        columna,
        numero_dia
    ):

        hoy = date.today()

        fecha_dia = date(
            self.anio_actual,
            self.mes_actual,
            numero_dia
        )

        es_hoy = (
            fecha_dia == hoy
        )

        fondo = (
            COLOR_DIA_HOY
            if es_hoy
            else COLOR_DIA
        )

        # --------------------------------------------------------
        # CELDA
        # --------------------------------------------------------

        celda = tk.Frame(
            self.contenedor_calendario,
            bg=fondo,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1,
            cursor="hand2"
        )

        celda.grid(
            row=fila,
            column=columna,
            sticky="nsew",
            padx=1,
            pady=1
        )

        # --------------------------------------------------------
        # NÚMERO DEL DÍA
        # --------------------------------------------------------

        numero = tk.Label(
            celda,
            text=str(numero_dia),
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            fg=(
                COLOR_AZUL
                if es_hoy
                else COLOR_TEXTO
            ),
            bg=fondo,
            anchor="w",
            cursor="hand2"
        )

        numero.pack(
            anchor="nw",
            padx=9,
            pady=7
        )

        # --------------------------------------------------------
        # ZONA DE GUARDIAS
        # --------------------------------------------------------

        zona_guardias = tk.Frame(
            celda,
            bg=fondo,
            cursor="hand2"
        )

        zona_guardias.pack(
            fill="both",
            expand=True,
            padx=7,
            pady=(0, 7)
        )

        # --------------------------------------------------------
        # OBTENER MÉDICOS DE ESE DÍA
        # --------------------------------------------------------

        guardias = self.guardias_mes.get(
            fecha_dia,
            []
        )

        # --------------------------------------------------------
        # SI NO HAY GUARDIAS
        # --------------------------------------------------------

        if not guardias:

            tk.Label(
                zona_guardias,
                text="Sin guardias",
                font=(
                    "Segoe UI",
                    8
                ),
                fg=COLOR_SECUNDARIO,
                bg=fondo,
                anchor="w",
                justify="left",
                cursor="hand2"
            ).pack(
                anchor="nw",
                pady=(5, 0)
            )

        # --------------------------------------------------------
        # MOSTRAR MÉDICOS
        # --------------------------------------------------------

        else:

            # Mostrar como máximo 3 médicos en la celda
            medicos_visibles = guardias[:3]

            for medico in medicos_visibles:

                nombre = medico["nombre"]

                esta_inactivo = medico.get(
                    "inactivo",
                    False
                )

                causa_inactividad = medico.get(
                    "causa_inactividad",
                    ""
                )

                # ------------------------------------------------
                # CONTENEDOR DEL MÉDICO
                # ------------------------------------------------

                frame_medico = tk.Frame(
                    zona_guardias,
                    bg=fondo,
                    cursor="hand2"
                )

                frame_medico.pack(
                    anchor="nw",
                    fill="x",
                    pady=(2, 3)
                )

                # ------------------------------------------------
                # NOMBRE
                # ------------------------------------------------

                etiqueta = tk.Label(
                    frame_medico,
                    text=f"Dr. {nombre}",
                    font=(
                        "Segoe UI",
                        8,
                        "bold"
                    ),
                    fg=COLOR_TEXTO,
                    bg=fondo,
                    anchor="w",
                    justify="left",
                    wraplength=170,
                    cursor="hand2"
                )

                etiqueta.pack(
                    anchor="nw",
                    fill="x"
                )

                # ------------------------------------------------
                # CAUSA DE INACTIVIDAD
                # ------------------------------------------------

                if esta_inactivo:

                    texto_inactividad = (
                        causa_inactividad
                        if causa_inactividad
                        else "Inactivo"
                    )

                    etiqueta_inactividad = tk.Label(
                        frame_medico,
                        text=texto_inactividad,
                        font=(
                            "Segoe UI",
                            8
                        ),
                        fg="#D97706",
                        bg=fondo,
                        anchor="w",
                        justify="left",
                        wraplength=170,
                        cursor="hand2"
                    )

                    etiqueta_inactividad.pack(
                        anchor="nw",
                        fill="x",
                        pady=(1, 0)
                    )

            # ------------------------------------------------
            # INDICADOR DE MÉDICOS RESTANTES
            # ------------------------------------------------

            cantidad_restante = len(guardias) - len(medicos_visibles)

            if cantidad_restante > 0:

                etiqueta_mas = tk.Label(
                    zona_guardias,
                    text=f"+{cantidad_restante}",
                    font=(
                        "Segoe UI",
                        8,
                        "bold"
                    ),
                    fg=COLOR_AZUL,
                    bg=fondo,
                    anchor="w",
                    justify="left",
                    cursor="hand2"
                )

                etiqueta_mas.pack(
                    anchor="nw",
                    pady=(2, 0)
                )

        # --------------------------------------------------------
        # CLICK EN EL DÍA
        # --------------------------------------------------------

        self.vincular_click_dia(
            celda,
            numero_dia
        )

    # ========================================================
    # CLICK EN DÍA
    # ========================================================

    def vincular_click_dia(
        self,
        widget,
        numero_dia
    ):

        widgets = [
            widget
        ]

        for hijo in widget.winfo_children():

            widgets.append(
                hijo
            )

            for nieto in hijo.winfo_children():

                widgets.append(
                    nieto
                )

        for elemento in widgets:

            elemento.bind(
                "<Button-1>",
                lambda e, dia=numero_dia:
                    self.seleccionar_dia(dia)
            )

    # ========================================================
    # SELECCIONAR DÍA
    # ========================================================

    def seleccionar_dia(
        self,
        numero_dia
    ):

        nombre_mes = self.obtener_nombre_mes(
            self.mes_actual
        )

        print(
            f"[Guardias] Día seleccionado: "
            f"{numero_dia}/{self.mes_actual}/{self.anio_actual}"
        )

        self.mostrar_mensaje_dia(
            numero_dia,
            nombre_mes
        )

    # ========================================================
    # MENSAJE TEMPORAL / DETALLE DEL DÍA
    # ========================================================

    def mostrar_mensaje_dia(
        self,
        numero_dia,
        nombre_mes
    ):

        # ========================================================
        # OBTENER MÉDICOS DEL DÍA
        # ========================================================

        fecha_dia = date(
            self.anio_actual,
            self.mes_actual,
            numero_dia
        )

        guardias_del_dia = self.guardias_mes.get(
            fecha_dia,
            []
        )

        # ========================================================
        # VENTANA MODAL
        # ========================================================

        ventana = tk.Toplevel(self)
        ventana.title("Detalles de Guardias")
        ventana.configure(bg=COLOR_FONDO)

        # Tamaño inicial
        ancho = 720
        alto = 620

        # ========================================================
        # CENTRAR VENTANA EN LA PANTALLA PRINCIPAL
        # ========================================================

        ventana.update_idletasks()

        ventana_principal = self.winfo_toplevel()

        x_principal = ventana_principal.winfo_x()
        y_principal = ventana_principal.winfo_y()

        ancho_principal = ventana_principal.winfo_width()
        alto_principal = ventana_principal.winfo_height()

        x = x_principal + (ancho_principal - ancho) // 2
        y = y_principal + (alto_principal - alto) // 2

        # Evitar posiciones negativas
        x = max(x, 0)
        y = max(y, 0)

        ventana.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

        ventana.minsize(
            650,
            500
        )

        ventana.transient(
            ventana_principal
        )

        ventana.grab_set()

        # ========================================================
        # ENCABEZADO GENERAL
        # ========================================================

        header = tk.Frame(
            ventana,
            bg=COLOR_BLANCO
        )

        header.pack(
            fill="x"
        )

        # ========================================================
        # PARTE SUPERIOR DEL ENCABEZADO
        # ========================================================

        header_superior = tk.Frame(
            header,
            bg=COLOR_BLANCO
        )

        header_superior.pack(
            fill="x",
            padx=25,
            pady=(20, 5)
        )

        # --------------------------------------------------------
        # TÍTULO
        # --------------------------------------------------------

        frame_titulo = tk.Frame(
            header_superior,
            bg=COLOR_BLANCO
        )

        frame_titulo.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Label(
            frame_titulo,
            text="Guardias del día",
            font=(
                "Segoe UI",
                11
            ),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame_titulo,
            text=f"{numero_dia} de {nombre_mes} de {self.anio_actual}",
            font=(
                "Segoe UI",
                20,
                "bold"
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(
            anchor="w",
            pady=(1, 0)
        )

        # ========================================================
        # BOTÓN EXPORTAR
        # ========================================================

        btn_exportar = tk.Button(
            header_superior,
            text="  Exportar",
            image=self.icon_exportar,
            compound="left",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg=COLOR_AZUL,
            fg="white",
            activebackground=COLOR_AZUL_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=lambda: mostrar_dialogo_exportar_guardias(
                fecha_obj=fecha_dia,
                medicos_guardia=guardias_del_dia,
                observaciones="",
                parent_window=ventana
            )
        )

        btn_exportar.pack(
            side="right",
            padx=(15, 0)
        )

        btn_exportar.bind(
            "<Enter>",
            lambda e: btn_exportar.config(
                bg=COLOR_AZUL_HOVER
            )
        )

        btn_exportar.bind(
            "<Leave>",
            lambda e: btn_exportar.config(
                bg=COLOR_AZUL
            )
        )

        # ========================================================
        # LÍNEA INFORMATIVA
        # ========================================================

        separador = tk.Frame(
            header,
            bg=COLOR_BORDE,
            height=1
        )

        separador.pack(
            fill="x",
            padx=25,
            pady=(12, 0)
        )

        # ========================================================
        # ÁREA PRINCIPAL
        # ========================================================

        frame_principal = tk.Frame(
            ventana,
            bg=COLOR_FONDO
        )

        frame_principal.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15
        )

        # ========================================================
        # TÍTULO DE LA LISTA
        # ========================================================

        frame_lista_titulo = tk.Frame(
            frame_principal,
            bg=COLOR_FONDO
        )

        frame_lista_titulo.pack(
            fill="x",
            pady=(0, 10)
        )

        cantidad = len(guardias_del_dia)

        tk.Label(
            frame_lista_titulo,
            text=f"Médicos en guardia ({cantidad})",
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO
        ).pack(
            side="left"
        )

        # ========================================================
        # CONTENEDOR DEL SCROLL
        # ========================================================

        frame_lista = tk.Frame(
            frame_principal,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        frame_lista.pack(
            fill="both",
            expand=True
        )

        canvas = tk.Canvas(
            frame_lista,
            bg=COLOR_BLANCO,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            frame_lista,
            orient="vertical",
            command=canvas.yview
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        contenido = tk.Frame(
            canvas,
            bg=COLOR_BLANCO
        )

        canvas_window = canvas.create_window(
            (0, 0),
            window=contenido,
            anchor="nw"
        )

        def configurar_scroll(event=None):

            canvas.configure(
                scrollregion=canvas.bbox("all")
            )

            canvas.itemconfig(
                canvas_window,
                width=canvas.winfo_width()
            )

        contenido.bind(
            "<Configure>",
            configurar_scroll
        )

        canvas.bind(
            "<Configure>",
            configurar_scroll
        )

        # ========================================================
        # SCROLL CON RUEDA
        # ========================================================

        def scroll_modal(event):

            canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

        canvas.bind(
            "<MouseWheel>",
            scroll_modal
        )

        # ========================================================
        # SIN GUARDIAS
        # ========================================================

        if not guardias_del_dia:

            vacio = tk.Frame(
                contenido,
                bg=COLOR_BLANCO
            )

            vacio.pack(
                fill="both",
                expand=True,
                pady=70
            )

            tk.Label(
                vacio,
                text="No hay médicos en guardia",
                font=(
                    "Segoe UI",
                    14,
                    "bold"
                ),
                fg=COLOR_TEXTO,
                bg=COLOR_BLANCO
            ).pack()

            tk.Label(
                vacio,
                text="No se encontraron guardias asignadas para este día.",
                font=(
                    "Segoe UI",
                    10
                ),
                fg=COLOR_SECUNDARIO,
                bg=COLOR_BLANCO
            ).pack(
                pady=(7, 0)
            )

        # ========================================================
        # MOSTRAR MÉDICOS
        # ========================================================

        else:

            for medico in guardias_del_dia:

                nombre = medico.get(
                    "nombre",
                    "Desconocido"
                )

                cargo = medico.get(
                    "cargo",
                    "Sin cargo asignado"
                )

                centro = medico.get(
                    "centro",
                    "Sin centro asignado"
                )

                telefono = medico.get(
                    "telefono",
                    "No registrado"
                )

                especialidad = medico.get(
                    "especialidad",
                    "Sin especialidad"
                )

                esta_inactivo = medico.get(
                    "inactivo",
                    False
                )

                causa = medico.get(
                    "causa_inactividad",
                    "Inactivo"
                )

                # =================================================
                # TARJETA
                # =================================================

                tarjeta = tk.Frame(
                    contenido,
                    bg="#F8FAFC",
                    highlightbackground=(
                        "#F59E0B"
                        if esta_inactivo
                        else COLOR_BORDE
                    ),
                    highlightthickness=1
                )

                tarjeta.pack(
                    fill="x",
                    padx=12,
                    pady=(6, 6)
                )

                # =================================================
                # ENCABEZADO DE LA TARJETA
                # =================================================

                encabezado_medico = tk.Frame(
                    tarjeta,
                    bg="#F8FAFC"
                )

                encabezado_medico.pack(
                    fill="x",
                    padx=16,
                    pady=(13, 8)
                )

                # -------------------------------------------------
                # NOMBRE
                # -------------------------------------------------

                tk.Label(
                    encabezado_medico,
                    text=f"Dr(a). {nombre}",
                    font=(
                        "Segoe UI",
                        13,
                        "bold"
                    ),
                    fg=COLOR_TEXTO,
                    bg="#F8FAFC"
                ).pack(
                    side="left"
                )

                # -------------------------------------------------
                # ESTADO
                # -------------------------------------------------

                if esta_inactivo:

                    tk.Label(
                        encabezado_medico,
                        text=" INACTIVA ",
                        font=(
                            "Segoe UI",
                            8,
                            "bold"
                        ),
                        fg="#B45309",
                        bg="#FEF3C7",
                        padx=7,
                        pady=3
                    ).pack(
                        side="right"
                    )

                else:

                    tk.Label(
                        encabezado_medico,
                        text=" ACTIVA ",
                        font=(
                            "Segoe UI",
                            8,
                            "bold"
                        ),
                        fg="#15803D",
                        bg="#DCFCE7",
                        padx=7,
                        pady=3
                    ).pack(
                        side="right"
                    )

                # =================================================
                # INFORMACIÓN
                # =================================================

                info = tk.Frame(
                    tarjeta,
                    bg="#F8FAFC"
                )

                info.pack(
                    fill="x",
                    padx=16,
                    pady=(0, 12)
                )

                # -------------------------------------------------
                # CENTRO
                # -------------------------------------------------

                frame_centro = tk.Frame(
                    info,
                    bg="#F8FAFC"
                )

                frame_centro.pack(
                    fill="x",
                    pady=3
                )

                tk.Label(
                    frame_centro,
                    text="Centro de salud",
                    font=(
                        "Segoe UI",
                        9,
                        "bold"
                    ),
                    fg=COLOR_SECUNDARIO,
                    bg="#F8FAFC",
                    width=18,
                    anchor="w"
                ).pack(
                    side="left"
                )

                tk.Label(
                    frame_centro,
                    text=centro or "No registrado",
                    font=(
                        "Segoe UI",
                        10
                    ),
                    fg=COLOR_TEXTO,
                    bg="#F8FAFC",
                    anchor="w",
                    justify="left",
                    wraplength=450
                ).pack(
                    side="left",
                    fill="x",
                    expand=True
                )

                # -------------------------------------------------
                # CARGO
                # -------------------------------------------------

                frame_cargo = tk.Frame(
                    info,
                    bg="#F8FAFC"
                )

                frame_cargo.pack(
                    fill="x",
                    pady=3
                )

                tk.Label(
                    frame_cargo,
                    text="Cargo",
                    font=(
                        "Segoe UI",
                        9,
                        "bold"
                    ),
                    fg=COLOR_SECUNDARIO,
                    bg="#F8FAFC",
                    width=18,
                    anchor="w"
                ).pack(
                    side="left"
                )

                tk.Label(
                    frame_cargo,
                    text=cargo or "No registrado",
                    font=(
                        "Segoe UI",
                        10
                    ),
                    fg=COLOR_TEXTO,
                    bg="#F8FAFC",
                    anchor="w",
                    justify="left",
                    wraplength=450
                ).pack(
                    side="left",
                    fill="x",
                    expand=True
                )

                # -------------------------------------------------
                # ESPECIALIDAD
                # -------------------------------------------------

                frame_especialidad = tk.Frame(
                    info,
                    bg="#F8FAFC"
                )

                frame_especialidad.pack(
                    fill="x",
                    pady=3
                )

                tk.Label(
                    frame_especialidad,
                    text="Especialidad",
                    font=(
                        "Segoe UI",
                        9,
                        "bold"
                    ),
                    fg=COLOR_SECUNDARIO,
                    bg="#F8FAFC",
                    width=18,
                    anchor="w"
                ).pack(
                    side="left"
                )

                tk.Label(
                    frame_especialidad,
                    text=especialidad or "No registrada",
                    font=(
                        "Segoe UI",
                        10
                    ),
                    fg=COLOR_TEXTO,
                    bg="#F8FAFC",
                    anchor="w",
                    justify="left",
                    wraplength=450
                ).pack(
                    side="left",
                    fill="x",
                    expand=True
                )

                # -------------------------------------------------
                # TELÉFONO
                # -------------------------------------------------

                frame_telefono = tk.Frame(
                    info,
                    bg="#F8FAFC"
                )

                frame_telefono.pack(
                    fill="x",
                    pady=3
                )

                tk.Label(
                    frame_telefono,
                    text="Teléfono",
                    font=(
                        "Segoe UI",
                        9,
                        "bold"
                    ),
                    fg=COLOR_SECUNDARIO,
                    bg="#F8FAFC",
                    width=18,
                    anchor="w"
                ).pack(
                    side="left"
                )

                tk.Label(
                    frame_telefono,
                    text=telefono or "No registrado",
                    font=(
                        "Segoe UI",
                        10
                    ),
                    fg=COLOR_TEXTO,
                    bg="#F8FAFC",
                    anchor="w"
                ).pack(
                    side="left"
                )

                # =================================================
                # ALERTA DE INACTIVIDAD
                # =================================================

                if esta_inactivo:

                    alerta = tk.Frame(
                        tarjeta,
                        bg="#FEF3C7"
                    )

                    alerta.pack(
                        fill="x",
                        padx=16,
                        pady=(0, 14)
                    )

                    tk.Label(
                        alerta,
                        text="⚠",
                        font=(
                            "Segoe UI",
                            11,
                            "bold"
                        ),
                        fg="#B45309",
                        bg="#FEF3C7"
                    ).pack(
                        side="left",
                        padx=(10, 5),
                        pady=7
                    )

                    tk.Label(
                        alerta,
                        text=f"Motivo: {causa or 'Inactividad registrada'}",
                        font=(
                            "Segoe UI",
                            9,
                            "bold"
                        ),
                        fg="#92400E",
                        bg="#FEF3C7",
                        anchor="w",
                        justify="left",
                        wraplength=550
                    ).pack(
                        side="left",
                        fill="x",
                        expand=True,
                        pady=7
                    )

        # ========================================================
        # PIE DE VENTANA
        # ========================================================

        footer = tk.Frame(
            ventana,
            bg=COLOR_BLANCO
        )

        footer.pack(
            fill="x"
        )

        tk.Frame(
            footer,
            bg=COLOR_BORDE,
            height=1
        ).pack(
            fill="x"
        )

        tk.Button(
            footer,
            text="Cerrar",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg="#E2E8F0",
            fg=COLOR_TEXTO,
            activebackground="#CBD5E1",
            activeforeground=COLOR_TEXTO,
            relief="flat",
            bd=0,
            padx=25,
            pady=8,
            cursor="hand2",
            command=ventana.destroy
        ).pack(
            side="right",
            padx=25,
            pady=12
        )


    # ========================================================
    # CAMBIAR MES
    # ========================================================

    def mes_anterior(self):

        self.mes_actual -= 1

        if self.mes_actual < 1:

            self.mes_actual = 12
            self.anio_actual -= 1

        self.crear_calendario()

    def mes_siguiente(self):

        self.mes_actual += 1

        if self.mes_actual > 12:

            self.mes_actual = 1
            self.anio_actual += 1

        self.crear_calendario()

    def ir_a_hoy(self):

        hoy = date.today()

        self.mes_actual = hoy.month
        self.anio_actual = hoy.year

        self.crear_calendario()

    def _cargos_seleccionados(self):
        """Devuelve el cargo seleccionado o 'Todos los cargos'."""
        cargo = self.cargo_var.get()
        if not cargo or cargo in ("Todos los cargos", "Guardias médicas"):
            return "Todos los cargos"
        return cargo

    def aplicar_filtros(self):

        self.crear_calendario()

    def exportar(self):
        """
        Si el filtro es "Guardias médicas" → exporta con el formato
        de grupos Artículo 8 (calendario con todos los nombres).
        Si no, usa la exportación normal de guardias del mes.
        """
        if self.cargo_var.get() == "Guardias médicas":
            # Exportación estilo grupos Artículo 8
            exportar_todos_los_grupos_pdf(
                anio=self.anio_actual,
                mes=self.mes_actual,
                parent_window=self.winfo_toplevel()
            )
        else:
            # Exportación normal de guardias
            mostrar_dialogo_exportar_guardias_mes(
                anio=self.anio_actual,
                mes=self.mes_actual,
                guardias_por_dia=self.guardias_mes,
                cargo=self._cargos_seleccionados(),
                especialidad=self.especialidad_var.get(),
                centro=self.centro_var.get(),
                texto_busqueda=self.busqueda_var.get(),
                parent_window=self.winfo_toplevel()
            )

    # ========================================================
    # NOMBRES DE MESES
    # ========================================================

    def obtener_nombre_mes(
        self,
        numero_mes
    ):

        meses = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre"
        ]

        return meses[
            numero_mes - 1
        ]

    # ========================================================
    # SCROLL
    # ========================================================

    def actualizar_scroll(self, event=None):

        self.canvas.configure(
            scrollregion=self.canvas.bbox(
                "all"
            )
        )

    def ajustar_ancho(self, event):

        self.canvas.itemconfig(
            self.canvas_window,
            width=event.width
        )

    def _scroll_mouse(self, event):

        self.canvas.yview_scroll(
            int(
                -1 * (event.delta / 120)
            ),
            "units"
        )