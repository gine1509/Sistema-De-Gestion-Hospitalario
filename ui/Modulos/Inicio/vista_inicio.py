import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from ui.iconos import obtener_icono
from services.medico_service import obtener_estadisticas_medicos
from services.guardia_service import obtener_resumen_guardias_hoy
from services.oficio_service import obtener_resumen_oficios
from services.personal_direccion_service import obtener_resumen_direccion_hoy

# ============================================================
# COLORES
# ============================================================

COLOR_FONDO = "#F4F7FB"

COLOR_TEXTO = "#000000"
COLOR_SECUNDARIO = "#64748B"

COLOR_BLANCO = "#FFFFFF"

COLOR_AZUL = "#2563EB"
COLOR_VERDE = "#16A34A"
COLOR_ROJO = "#DC2626"
COLOR_AMARILLO = "#F59E0B"
COLOR_MORADO = "#7C3AED"

COLOR_BORDE = "#D8E0EA"

COLOR_HOVER = "#F8FAFC"
COLOR_PRESIONADO = "#F1F5F9"


# ============================================================
# CARGAR ICONO
# ============================================================

def cargar_icono(ruta, tamaño=28):

    try:

        imagen = Image.open(ruta)

        imagen = imagen.resize(
            (tamaño, tamaño),
            Image.Resampling.LANCZOS
        )

        return ImageTk.PhotoImage(imagen)

    except Exception:

        print(
            f"No se pudo cargar el icono: {ruta}"
        )

        return None


# ============================================================
# TARJETA DE ESTADÍSTICA
# ============================================================

class TarjetaEstadistica(tk.Frame):

    def __init__(
        self,
        parent,
        titulo,
        valor,
        icono,
        color,
        comando=None
    ):

        super().__init__(
            parent,
            bg="#FFFFFF",
            highlightbackground="#D8E0EA",
            highlightthickness=1,
            relief="raised",
            bd=1,
            height=135,
            cursor="hand2"
        )
        
        

        # ====================================================
        # DATOS
        # ====================================================

        self.comando = comando
        self.color_icono = color

        # Referencia de animación
        self.animacion_id = None

        # Estado de la tarjeta
        self.presionada = False
        self.mouse_dentro = False

        # Altura fija
        self.pack_propagate(False)

        # ====================================================
        # CONTENEDOR PRINCIPAL
        # ====================================================

        self.contenido = tk.Frame(
            self,
            bg=COLOR_BLANCO,
            cursor="hand2"
        )

        self.contenido.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(16, 16)
        )

        # ====================================================
        # ICONO
        # ====================================================

        self.icono_frame = tk.Frame(
            self.contenido,
            bg=color,
            width=54,
            height=54,
            cursor="hand2"
        )

        self.icono_frame.pack(
            side="left",
            anchor="center"
        )

        self.icono_frame.pack_propagate(False)

        # ----------------------------------------------------
        # Imagen del icono
        # ----------------------------------------------------

        self.icono_label = None

        if icono:

            self.icono_label = tk.Label(
                self.icono_frame,
                image=icono,
                bg=color,
                cursor="hand2"
            )

            self.icono_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

        # ====================================================
        # INFORMACIÓN
        # ====================================================

        self.informacion = tk.Frame(
            self.contenido,
            bg=COLOR_BLANCO,
            cursor="hand2"
        )

        self.informacion.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(12, 0)
        )

        # ====================================================
        # TÍTULO
        # ====================================================

        self.titulo_label = tk.Label(
            self.informacion,
            text=titulo,
            font=("Segoe UI", 8, "bold"),
            bg=COLOR_BLANCO,
            fg=COLOR_SECUNDARIO,
            cursor="hand2",
            wraplength=115,
            justify="left",
            anchor="w"
        )

        self.titulo_label.pack(
            anchor="w",
            fill="x"
        )

        # ====================================================
        # VALOR
        # ====================================================

        self.valor_label = tk.Label(
            self.informacion,
            text=str(valor),
            font=("Segoe UI", 25, "bold"),
            bg=COLOR_BLANCO,
            fg=COLOR_TEXTO,
            cursor="hand2"
        )

        self.valor_label.pack(
            anchor="w",
            pady=(3, 0)
        )

        # ====================================================
        # WIDGETS QUE FORMAN PARTE DE LA TARJETA
        # ====================================================

        self.widgets = [
            self,
            self.contenido,
            self.informacion,
            self.titulo_label,
            self.valor_label,
            self.icono_frame
        ]

        if self.icono_label:

            self.widgets.append(
                self.icono_label
            )

        # ====================================================
        # EVENTOS
        # ====================================================

        for widget in self.widgets:

            # Entrar
            widget.bind(
                "<Enter>",
                self.entrar
            )

            # Salir
            widget.bind(
                "<Leave>",
                self.salir
            )

            # Presionar
            widget.bind(
                "<ButtonPress-1>",
                self.presionar
            )

            # Soltar
            widget.bind(
                "<ButtonRelease-1>",
                self.soltar
            )

    # ========================================================
    # CAMBIAR FONDO
    # ========================================================

    def cambiar_fondo(self, color):

        widgets_fondo = [
            self,
            self.contenido,
            self.informacion,
            self.titulo_label,
            self.valor_label
        ]

        for widget in widgets_fondo:

            try:

                widget.configure(
                    bg=color
                )

            except tk.TclError:

                pass

    # ========================================================
    # HOVER
    # ========================================================

    def entrar(self, event=None):

        self.mouse_dentro = True

        if self.presionada:

            return

        self.cambiar_fondo(
            COLOR_HOVER
        )

        self.configure(
            highlightbackground="#B8C5D6",
            highlightthickness=2
        )

    # ========================================================
    # SALIR
    # ========================================================

    def salir(self, event=None):

        self.mouse_dentro = False

        if self.presionada:

            return

        self.cambiar_fondo(
            COLOR_BLANCO
        )

        self.configure(
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

    # ========================================================
    # PRESIONAR
    # ========================================================

    def presionar(self, event=None):

        if self.presionada:

            return

        self.presionada = True

        # Cancelar animación anterior
        if self.animacion_id:

            try:

                self.after_cancel(
                    self.animacion_id
                )

            except:

                pass

            self.animacion_id = None

        # Cambiar apariencia
        self.cambiar_fondo(
            COLOR_PRESIONADO
        )

        self.configure(
            highlightbackground="#94A3B8",
            highlightthickness=2
        )

        # Iniciar animación
        self.animar_hacia_abajo(
            paso=0
        )

    # ========================================================
    # ANIMACIÓN HACIA ABAJO
    # ========================================================

    def animar_hacia_abajo(self, paso=0):

        # 5 pasos de animación
        max_pasos = 5

        if paso > max_pasos:

            return

        # Valores:
        #
        # 16 / 16
        # 17 / 15
        # 18 / 14
        # 19 / 13
        # 20 / 12
        #
        # El contenido se desplaza hacia abajo
        # sin modificar el tamaño total.

        arriba = 16 + paso
        abajo = 16 - paso

        self.contenido.pack_configure(
            pady=(arriba, abajo)
        )

        self.animacion_id = self.after(
            15,
            lambda: self.animar_hacia_abajo(
                paso + 1
            )
        )

    # ========================================================
    # SOLTAR
    # ========================================================

    def soltar(self, event=None):

        if not self.presionada:

            return

        self.presionada = False

        # Cancelar animación
        if self.animacion_id:

            try:

                self.after_cancel(
                    self.animacion_id
                )

            except:

                pass

            self.animacion_id = None

        # Ejecutar animación de regreso
        self.animar_hacia_arriba(
            paso=5
        )

        # Restaurar borde
        self.configure(
            highlightbackground=(
                "#CBD5E1"
                if self.mouse_dentro
                else COLOR_BORDE
            ),
            highlightthickness=1
        )

        # Restaurar fondo
        if self.mouse_dentro:

            self.cambiar_fondo(
                COLOR_HOVER
            )

        else:

            self.cambiar_fondo(
                COLOR_BLANCO
            )

        # ====================================================
        # EJECUTAR COMANDO
        # ====================================================

        if self.comando:

            self.comando()

    # ========================================================
    # ANIMACIÓN HACIA ARRIBA
    # ========================================================

    def animar_hacia_arriba(self, paso=5):

        if paso < 0:

            self.contenido.pack_configure(
                pady=(16, 16)
            )

            self.animacion_id = None

            return

        arriba = 16 + paso
        abajo = 16 - paso

        self.contenido.pack_configure(
            pady=(arriba, abajo)
        )

        self.animacion_id = self.after(
            15,
            lambda: self.animar_hacia_arriba(
                paso - 1
            )
        )


# ============================================================
# VISTA INICIO
# ============================================================

class VistaInicio(tk.Frame):

    def __init__(
        self,
        parent,
        mostrar_medicos=None,
        mostrar_guardias=None,
        mostrar_oficios=None,
        mostrar_direccion=None
    ):
        super().__init__(
            parent,
            bg=COLOR_FONDO
        )

        self.mostrar_medicos = mostrar_medicos
        self.mostrar_guardias = mostrar_guardias
        self.mostrar_oficios = mostrar_oficios
        self.mostrar_direccion = mostrar_direccion
        self.iconos = {}

        # Obtener estadísticas desde la BD
        self.estadisticas = obtener_estadisticas_medicos()
        self.resumen_guardias = obtener_resumen_guardias_hoy()
        self.resumen_oficios = obtener_resumen_oficios()
        self.resumen_direccion = obtener_resumen_direccion_hoy()

        self.crear_interfaz()

    # ========================================================
    # TÍTULO DE SECCIÓN (reutilizable para cada módulo)
    # ========================================================

    def _crear_titulo_seccion(self, contenedor, titulo, subtitulo):

        tk.Label(
            contenedor,
            text=titulo,
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO
        ).pack(
            anchor="w"
        )

        tk.Label(
            contenedor,
            text=subtitulo,
            font=("Segoe UI", 10),
            bg=COLOR_FONDO,
            fg=COLOR_SECUNDARIO
        ).pack(
            anchor="w",
            pady=(3, 15)
        )

    # ========================================================
    # FILA DE TARJETAS (reutilizable para cada módulo)
    # ========================================================

    def _crear_fila_tarjetas(self, contenedor, tarjetas_info):
        """
        tarjetas_info: lista de tuplas
        (titulo, valor, icono, color, comando)
        """

        fila = tk.Frame(
            contenedor,
            bg=COLOR_FONDO
        )

        fila.pack(
            fill="x"
        )

        total = len(tarjetas_info)

        for indice, (
            titulo,
            valor,
            icono,
            color,
            comando
        ) in enumerate(tarjetas_info):

            tarjeta = TarjetaEstadistica(
                fila,
                titulo,
                valor,
                icono,
                color,
                comando
            )

            if indice == 0:
                relleno = (0, 6)
            elif indice == total - 1:
                relleno = (6, 0)
            else:
                relleno = (6, 6)

            tarjeta.grid(
                row=0,
                column=indice,
                sticky="ew",
                padx=relleno
            )

        for indice in range(total):

            fila.grid_columnconfigure(
                indice,
                weight=1,
                uniform=f"fila{id(fila)}"
            )

        return fila

    # ========================================================
    # LEYENDA (texto informativo bajo una fila de tarjetas)
    # ========================================================

    def _crear_leyenda(self, contenedor, texto):

        tk.Label(
            contenedor,
            text=texto,
            font=("Segoe UI", 9),
            bg=COLOR_FONDO,
            fg=COLOR_SECUNDARIO,
            wraplength=1200,
            justify="left",
            anchor="w"
        ).pack(
            anchor="w",
            pady=(8, 0)
        )

    # ========================================================
    # ESPACIADOR ENTRE SECCIONES
    # ========================================================

    def _crear_espaciador(self, contenedor, alto=30):

        tk.Frame(
            contenedor,
            bg=COLOR_FONDO,
            height=alto
        ).pack()

    # ========================================================
    # CREAR INTERFAZ
    # ========================================================

    def crear_interfaz(self):

        # ====================================================
        # FOOTER
        # ====================================================

        footer = tk.Frame(
            self,
            bg=COLOR_BLANCO,
            height=42,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        footer.pack(
            side="bottom",
            fill="x"
        )

        footer.pack_propagate(False)

        # ----------------------------------------------------
        # COPYRIGHT
        # ----------------------------------------------------

        tk.Label(
            footer,
            text="© 2026",
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_BLANCO,
            fg="#94A3B8"
        ).pack(
            side="left",
            padx=(25, 5)
        )

        # ----------------------------------------------------
        # NOMBRE DEL SISTEMA
        # ----------------------------------------------------

        tk.Label(
            footer,
            text="Sistema Gestión Hospitalaria",
            font=("Segoe UI", 9),
            bg=COLOR_BLANCO,
            fg="#94A3B8"
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # DEPARTAMENTO
        # ----------------------------------------------------

        tk.Label(
            footer,
            text="Departamento de Dirección",
            font=("Segoe UI", 9),
            bg=COLOR_BLANCO,
            fg="#94A3B8"
        ).pack(
            side="right",
            padx=25
        )

        # ====================================================
        # LIENZO CON SCROLL (para que quepan todos los módulos)
        # ====================================================

        self.canvas = tk.Canvas(
            self,
            bg=COLOR_FONDO,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.frame_scroll = tk.Frame(
            self.canvas,
            bg=COLOR_FONDO
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.frame_scroll,
            anchor="nw"
        )

        self.frame_scroll.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(
                self.canvas_window,
                width=e.width
            )
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(
                int(-1 * (e.delta / 120)),
                "units"
            )
        )

        # ====================================================
        # CONTENEDOR PRINCIPAL
        # ====================================================

        contenedor = tk.Frame(
            self.frame_scroll,
            bg=COLOR_FONDO
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=30
        )

        # ====================================================
        # ENCABEZADO
        # ====================================================

        tk.Label(
            contenedor,
            text="Panel Principal",
            font=("Segoe UI", 28, "bold"),
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO
        ).pack(
            anchor="w"
        )

        tk.Label(
            contenedor,
            text="Resumen general de la Gestión Hospitalaria",
            font=("Segoe UI", 11),
            bg=COLOR_FONDO,
            fg=COLOR_SECUNDARIO
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

        # ====================================================
        # ESPACIO
        # ====================================================

        tk.Frame(
            contenedor,
            bg=COLOR_FONDO,
            height=30
        ).pack()

        # ====================================================
        # TÍTULO ESTADÍSTICAS
        # ====================================================

        tk.Label(
            contenedor,
            text="Resumen de médicos",
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO
        ).pack(
            anchor="w"
        )

        tk.Label(
            contenedor,
            text=(
                "Seleccione una opción para consultar "
                "y gestionar la información"
            ),
            font=("Segoe UI", 10),
            bg=COLOR_FONDO,
            fg=COLOR_SECUNDARIO
        ).pack(
            anchor="w",
            pady=(3, 15)
        )
       
        # ====================================================
        # ICONOS
        # ====================================================
        self.iconos = {
            "medicos": obtener_icono("medicos", 28),
            "activos": obtener_icono("usuarios", 28),
            "inactivos": obtener_icono("inactivos", 28),
            "especialidades": obtener_icono("especialidades", 28),
            "art8": obtener_icono("art8", 28),
            "guardias_hoy": obtener_icono("guardias", 28),
            "guardias_especialidades": obtener_icono("especialidades", 28),
            "oficios_total": obtener_icono("oficios", 28),
            "oficios_ultimo": obtener_icono("agregar_oficio", 28),
            "direccion_total": obtener_icono("direccion", 28),
            "direccion_hoy": obtener_icono("horario", 28)
        }

        # ====================================================
        # CONTENEDOR DE TARJETAS
        # ====================================================

        tarjetas = tk.Frame(
            contenedor,
            bg=COLOR_FONDO
        )

        tarjetas.pack(
            fill="x"
        )

        # ====================================================
        # TARJETA 1
        # ====================================================

        tarjeta1 = TarjetaEstadistica(
            tarjetas,
            "Médicos registrados",
            self.estadisticas["total"],
            self.iconos["medicos"],
            COLOR_AZUL,
            lambda: self.mostrar_medicos("todos")
        )

        tarjeta1.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6)
        )

        # ====================================================
        # TARJETA 2
        # ====================================================

        tarjeta2 = TarjetaEstadistica(
            tarjetas,
            "Médicos activos",
            self.estadisticas["activos"],
            self.iconos["activos"],
            COLOR_VERDE,
            lambda: self.mostrar_medicos("activos")
        )

        tarjeta2.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=6
        )

        # ====================================================
        # TARJETA 3
        # ====================================================

        tarjeta3 = TarjetaEstadistica(
            tarjetas,
            "Médicos inactivos",
            self.estadisticas["inactivos"],
            self.iconos["inactivos"],
            COLOR_ROJO,
            lambda: self.mostrar_medicos("inactivos")
        )

        tarjeta3.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=6
        )

        # ====================================================
        # TARJETA 4
        # ====================================================

        tarjeta4 = TarjetaEstadistica(
            tarjetas,
            "Especialistas",
            self.estadisticas["especialistas"],
            self.iconos["especialidades"],
            COLOR_AMARILLO,
            lambda: self.mostrar_medicos("especialistas")
        )

        tarjeta4.grid(
            row=0,
            column=3,
            sticky="ew",
            padx=6
        )

        # ====================================================
        # TARJETA 5 - ARTÍCULO 8
        # ====================================================

        tarjeta5 = TarjetaEstadistica(
            tarjetas,
            "Médicos Art. 8",
            self.estadisticas["art8"],
            self.iconos["art8"],
            COLOR_MORADO,
            lambda: self.mostrar_medicos("art8")
        )

        tarjeta5.grid(
            row=0,
            column=4,
            sticky="ew",
            padx=(6, 0)
        )

        # ====================================================
        # COLUMNAS RESPONSIVAS
        # ====================================================

        for i in range(5):

            tarjetas.grid_columnconfigure(
                i,
                weight=1,
                uniform="tarjetas"
            )

        # ====================================================
        # RESUMEN DE GUARDIAS
        # ====================================================

        self._crear_espaciador(contenedor, 30)

        self._crear_titulo_seccion(
            contenedor,
            "Resumen de guardias",
            "Personal médico de guardia el día de hoy"
        )

        self._crear_fila_tarjetas(
            contenedor,
            [
                (
                    "Médicos de guardia hoy",
                    self.resumen_guardias["cantidad"],
                    self.iconos["guardias_hoy"],
                    COLOR_AZUL,
                    (
                        lambda: self.mostrar_guardias()
                        if self.mostrar_guardias
                        else None
                    )
                ),
                (
                    "Especialidades cubiertas hoy",
                    self.resumen_guardias["especialidades"],
                    self.iconos["guardias_especialidades"],
                    COLOR_MORADO,
                    (
                        lambda: self.mostrar_guardias()
                        if self.mostrar_guardias
                        else None
                    )
                )
            ]
        )

        if self.resumen_guardias["nombres"]:

            self._crear_leyenda(
                contenedor,
                "Hoy: "
                + ", ".join(self.resumen_guardias["nombres"])
            )

        else:

            self._crear_leyenda(
                contenedor,
                "No hay médicos de guardia registrados "
                "para el día de hoy."
            )

        # ====================================================
        # RESUMEN DE OFICIOS
        # ====================================================

        self._crear_espaciador(contenedor, 30)

        self._crear_titulo_seccion(
            contenedor,
            "Resumen de oficios",
            "Control del libro de oficios enviados"
        )

        self._crear_fila_tarjetas(
            contenedor,
            [
                (
                    "Oficios registrados",
                    self.resumen_oficios["total"],
                    self.iconos["oficios_total"],
                    COLOR_AZUL,
                    (
                        lambda: self.mostrar_oficios()
                        if self.mostrar_oficios
                        else None
                    )
                ),
                (
                    "Último oficio",
                    self.resumen_oficios["ultimo_numero"],
                    self.iconos["oficios_ultimo"],
                    COLOR_AMARILLO,
                    (
                        lambda: self.mostrar_oficios()
                        if self.mostrar_oficios
                        else None
                    )
                )
            ]
        )

        if self.resumen_oficios["ultimo_fecha"]:

            self._crear_leyenda(
                contenedor,
                "Último registrado: N° {numero} — {destinatario} ({fecha})".format(
                    numero=self.resumen_oficios["ultimo_numero"],
                    destinatario=(
                        self.resumen_oficios["ultimo_destinatario"]
                        or "sin destinatario"
                    ),
                    fecha=self.resumen_oficios["ultimo_fecha"].strftime(
                        "%d/%m/%Y"
                    )
                )
            )

        else:

            self._crear_leyenda(
                contenedor,
                "Aún no hay oficios registrados en el sistema."
            )

        # ====================================================
        # RESUMEN DE DIRECCIÓN
        # ====================================================

        self._crear_espaciador(contenedor, 30)

        self._crear_titulo_seccion(
            contenedor,
            "Resumen de dirección",
            "Personal administrativo y horarios del día"
        )

        self._crear_fila_tarjetas(
            contenedor,
            [
                (
                    "Personal de dirección",
                    self.resumen_direccion["total_activo"],
                    self.iconos["direccion_total"],
                    COLOR_AZUL,
                    (
                        lambda: self.mostrar_direccion()
                        if self.mostrar_direccion
                        else None
                    )
                ),
                (
                    "Con horario hoy",
                    self.resumen_direccion["cantidad_hoy"],
                    self.iconos["direccion_hoy"],
                    COLOR_VERDE,
                    (
                        lambda: self.mostrar_direccion()
                        if self.mostrar_direccion
                        else None
                    )
                )
            ]
        )

        if self.resumen_direccion["nombres_hoy"]:

            self._crear_leyenda(
                contenedor,
                "Hoy: "
                + ", ".join(self.resumen_direccion["nombres_hoy"])
            )

        elif self.resumen_direccion["es_fin_de_semana"]:

            self._crear_leyenda(
                contenedor,
                "No hay horarios asignados: el personal de "
                "dirección labora de lunes a viernes."
            )

        else:

            self._crear_leyenda(
                contenedor,
                "Nadie tiene horario asignado para el día de hoy."
            )

        # ====================================================
        # INFORMACIÓN INFERIOR
        # ====================================================

        self._crear_espaciador(contenedor, 20)

        tk.Frame(
            contenedor,
            bg=COLOR_BORDE,
            height=1
        ).pack(
            fill="x"
        )