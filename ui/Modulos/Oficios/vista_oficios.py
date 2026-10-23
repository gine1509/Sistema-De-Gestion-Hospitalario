import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from services.oficio_service import (
    listar_oficios,
    obtener_oficio,
    eliminar_oficio as servicio_eliminar_oficio
)

from ui.mensajes import (
    mostrar_pregunta,
    mostrar_exito,
    mostrar_error
)

from ui.iconos import obtener_icono

from .colores import (
    COLOR_FONDO,
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
    COLOR_BORDE
)

from .formulario_oficio import VentanaFormularioOficio
from .tarjeta_oficio import TarjetaOficio
from .detalle_oficio import VentanaDetalleOficio


class VistaOficios(tk.Frame):

    def __init__(self, parent):

        super().__init__(
            parent,
            bg=COLOR_FONDO
        )

        self.pack(
            fill="both",
            expand=True
        )

        self.icon_agregar = obtener_icono(
            "agregar_oficio",
            18
        )

        self.icon_buscar = obtener_icono(
            "buscar",
            16
        )

        self.oficios = []
        self.columnas_actuales = 0
        self._redibujando_grid = False

        self.crear_interfaz()
        self.cargar_oficios()

    # ========================================================
    # INTERFAZ
    # ========================================================

    def crear_interfaz(self):

        # ----------------------------------------------------
        # CONTENEDOR CON SCROLL
        # ----------------------------------------------------

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
            self._scroll_mouse
        )

        # ----------------------------------------------------
        # CONTENIDO
        # ----------------------------------------------------

        contenido = tk.Frame(
            self.frame_scroll,
            bg=COLOR_FONDO
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25
        )

        # ----------------------------------------------------
        # ENCABEZADO
        # ----------------------------------------------------

        encabezado = tk.Frame(
            contenido,
            bg=COLOR_FONDO
        )

        encabezado.pack(
            fill="x",
            pady=(0, 20)
        )

        tk.Label(
            encabezado,
            text="Control de Oficios",
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO,
            font=("Segoe UI", 20, "bold")
        ).pack(
            side="left"
        )

        ctk.CTkButton(
            encabezado,
            text="Nuevo oficio",
            image=self.icon_agregar,
            compound="left",
            width=170,
            height=38,
            corner_radius=8,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,
            font=("Segoe UI", 14, "bold"),
            command=self.abrir_formulario_nuevo
        ).pack(
            side="right"
        )

        # ----------------------------------------------------
        # BARRA DE BÚSQUEDA
        # ----------------------------------------------------

        barra_busqueda = tk.Frame(
            contenido,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        barra_busqueda.pack(
            fill="x",
            pady=(0, 15)
        )

        if self.icon_buscar:

            tk.Label(
                barra_busqueda,
                image=self.icon_buscar,
                bg=COLOR_BLANCO
            ).pack(
                side="left",
                padx=(12, 5),
                pady=8
            )

        self.entry_busqueda = tk.Entry(
            barra_busqueda,
            bg=COLOR_BLANCO,
            fg="#94A3B8",
            relief="flat",
            font=("Segoe UI", 12)
        )

        self.entry_busqueda.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 12),
            pady=8
        )

        self.entry_busqueda.insert(
            0,
            "Buscar por número, destinatario, asunto u observación..."
        )
        
        self.entry_busqueda.configure(
            fg="#94A3B8"
        )

        self.entry_busqueda.bind(
            "<FocusIn>",
            self._limpiar_placeholder
        )

        self.entry_busqueda.bind(
            "<KeyRelease>",
            lambda e: self.aplicar_busqueda()
        )

        # ----------------------------------------------------
        # CONTADOR
        # ----------------------------------------------------

        self.label_contador = tk.Label(
            contenido,
            text="",
            bg=COLOR_FONDO,
            fg=COLOR_SECUNDARIO,
            font=("Segoe UI", 11)
        )

        self.label_contador.pack(
            anchor="w",
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # CONTENEDOR DE TARJETAS
        # ----------------------------------------------------

        self.frame_lista = tk.Frame(
            contenido,
            bg=COLOR_FONDO
        )

        self.frame_lista.pack(
            fill="both",
            expand=True
        )
        
        self.frame_lista.bind(
            "<Configure>",
            lambda e: self._ajustar_columnas()
        )

    # ========================================================
    # SCROLL
    # ========================================================

    def _scroll_mouse(self, event):

        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    # ========================================================
    # PLACEHOLDER
    # ========================================================

    def _limpiar_placeholder(self, event):

        if self.entry_busqueda.get().startswith(
            "Buscar por número"
        ):

            self.entry_busqueda.delete(
                0,
                "end"
            )

            self.entry_busqueda.configure(
                fg=COLOR_TEXTO
            )

    # ========================================================
    # CARGAR OFICIOS
    # ========================================================

    def cargar_oficios(self):

        try:

            self.oficios = listar_oficios()

            # ====================================================
            # ORDENAR DEL ÚLTIMO REGISTRADO AL MÁS ANTIGUO
            # ====================================================

            self.oficios.sort(
                key=lambda oficio: (
                    oficio.get("id_oficio", 0)
                    if isinstance(oficio, dict)
                    else getattr(oficio, "id_oficio", 0)
                ),
                reverse=True
            )

        except Exception as error:

            print(
                f"[VistaOficios] Error cargando oficios: {error}"
            )

            self.oficios = []

        self._pintar_tarjetas(
            self.oficios
        )

    # ========================================================
    # BUSCAR
    # ========================================================

    def aplicar_busqueda(self):

        texto = self.entry_busqueda.get().strip()

        if texto.startswith(
            "Buscar por número"
        ):

            texto = ""

        try:

            resultados = listar_oficios(
                texto
            )

            # ====================================================
            # ORDENAR DEL ÚLTIMO REGISTRADO AL MÁS ANTIGUO
            # ====================================================

            resultados.sort(
                key=lambda oficio: (
                    oficio.get("id_oficio", 0)
                    if isinstance(oficio, dict)
                    else getattr(oficio, "id_oficio", 0)
                ),
                reverse=True
            )

        except Exception as error:

            print(
                f"[VistaOficios] Error buscando oficios: {error}"
            )

            resultados = []

        self._pintar_tarjetas(
            resultados
        )

    # ========================================================
    # PINTAR TARJETAS
    # ========================================================

    def _pintar_tarjetas(self, oficios):

        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        cantidad = len(oficios)

        self.label_contador.configure(
            text=(
                f"{cantidad} oficio"
                f"{'s' if cantidad != 1 else ''} "
                f"registrado"
                f"{'s' if cantidad != 1 else ''}"
            )
        )

        if cantidad == 0:

            tk.Label(
                self.frame_lista,
                text="No hay oficios que coincidan con la búsqueda.",
                bg=COLOR_FONDO,
                fg=COLOR_SECUNDARIO,
                font=("Segoe UI", 12),
                pady=40
            ).pack(
                fill="x"
            )

            self.columnas_actuales = 0
            return

        ancho = self.frame_lista.winfo_width()

        if ancho <= 1:
            self.after(
                100,
                lambda: self._pintar_tarjetas(oficios)
            )
            return

        ancho_tarjeta = 320
        espacio = 16

        columnas = max(
            1,
            min(
                4,
                ancho // (ancho_tarjeta + espacio)
            )
        )

        self.columnas_actuales = columnas

        self._redibujando_grid = True

        for columna in range(columnas):

            self.frame_lista.grid_columnconfigure(
                columna,
                weight=0
            )

        for indice, oficio in enumerate(oficios):

            fila = indice // columnas
            columna = indice % columnas

            tarjeta = TarjetaOficio(
                self.frame_lista,
                oficio,
                al_ver_detalle=self.abrir_detalle
            )

            tarjeta.grid(
                row=fila,
                column=columna,
                padx=8,
                pady=8,
                sticky="nw"
            )

        self._redibujando_grid = False
        
    def _ajustar_columnas(self):

        if self._redibujando_grid:
            return

        if not self.oficios:
            return

        ancho = self.frame_lista.winfo_width()

        if ancho <= 1:
            return

        ancho_tarjeta = 350
        espacio = 16

        nuevas_columnas = max(
            1,
            min(
                4,
                ancho // (ancho_tarjeta + espacio)
            )
        )

        if nuevas_columnas != self.columnas_actuales:

            self.columnas_actuales = 0

            self._pintar_tarjetas(
                self.oficios
            )

        # ========================================================
    # VER DETALLE
    # ========================================================

    def abrir_detalle(self, oficio):

        # ----------------------------------------------------
        # OBTENER ID DEL OFICIO
        # ----------------------------------------------------

        # Si viene como diccionario
        if isinstance(oficio, dict):

            id_oficio = oficio.get(
                "id_oficio"
            )

        # Si ya viene como objeto Oficio
        else:

            id_oficio = getattr(
                oficio,
                "id_oficio",
                None
            )

        # ----------------------------------------------------
        # OBTENER OFICIO COMPLETO
        # ----------------------------------------------------

        if id_oficio:

            try:

                oficio_completo = obtener_oficio(
                    id_oficio
                )

                if oficio_completo:

                    oficio = oficio_completo

            except Exception as error:

                print(
                    f"[VistaOficios] Error obteniendo "
                    f"detalle: {error}"
                )

        # ----------------------------------------------------
        # ABRIR DETALLE
        # ----------------------------------------------------

        VentanaDetalleOficio(
            self,
            oficio,
            al_editar=self.editar_desde_detalle,
            al_eliminar=self.eliminar_desde_detalle
        )

    # ========================================================
    # EDITAR DESDE DETALLE
    # ========================================================

    def editar_desde_detalle(self, oficio):

        # Obtener ID
        id_oficio = getattr(
            oficio,
            "id_oficio",
            None
        )

        if not id_oficio:

            mostrar_error(
                self,
                mensaje="No se pudo identificar el oficio."
            )

            return

        # Abrir formulario de edición
        self.abrir_formulario_editar(
            id_oficio
        )

    # ========================================================
    # ELIMINAR DESDE DETALLE
    # ========================================================

    def eliminar_desde_detalle(self, oficio):

        # Obtener ID
        id_oficio = getattr(
            oficio,
            "id_oficio",
            None
        )

        # Obtener número
        numero = getattr(
            oficio,
            "numero",
            ""
        )

        if not id_oficio:

            mostrar_error(
                self,
                mensaje="No se pudo identificar el oficio."
            )

            return

        # Usamos la función de eliminación
        # que ya tienes implementada.
        self.eliminar(
            id_oficio,
            numero
        )

    # ========================================================
    # NUEVO
    # ========================================================

    def abrir_formulario_nuevo(self):

        VentanaFormularioOficio(
            self,
            al_guardar=self.cargar_oficios
        )

    # ========================================================
    # EDITAR
    # ========================================================

    def abrir_formulario_editar(
        self,
        id_oficio
    ):

        oficio = obtener_oficio(
            id_oficio
        )

        if not oficio:

            mostrar_error(
                self,
                mensaje="El oficio ya no existe."
            )

            self.cargar_oficios()

            return

        VentanaFormularioOficio(
            self,
            al_guardar=self.cargar_oficios,
            oficio_editar=oficio
        )

    # ========================================================
    # ELIMINAR
    # ========================================================

    def eliminar(
        self,
        id_oficio,
        numero
    ):

        confirmado = mostrar_pregunta(
            self,
            titulo="Eliminar oficio",
            mensaje=(
                f"¿Deseas eliminar el oficio N° "
                f"{numero}? Esta acción no se puede deshacer."
            )
        )

        if not confirmado:
            return

        try:

            servicio_eliminar_oficio(
                id_oficio
            )

            mostrar_exito(
                self,
                mensaje="El oficio se eliminó correctamente."
            )

            self.cargar_oficios()

        except Exception as error:

            mostrar_error(
                self,
                mensaje=(
                    f"No se pudo eliminar el oficio.\n"
                    f"{error}"
                )
            )