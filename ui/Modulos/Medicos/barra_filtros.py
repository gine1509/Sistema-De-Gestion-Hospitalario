import tkinter as tk
from tkinter import ttk

from ui.iconos import obtener_icono
from .colores import (
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_BORDE
)


PLACEHOLDER_BUSQUEDA = "Buscar por nombre, apellido o cédula..."


class BarraFiltros(tk.Frame):
    """
    Barra de búsqueda y filtros para médicos.

    Buscador:
        - Nombre
        - Apellido
        - Cédula

    Filtros:
        - Dependencia
        - Cargo
        - Centro de salud
        - Estatus

    Los cargos y centros se cargan dinámicamente desde
    los médicos existentes.
    """

    def __init__(
        self,
        parent,
        al_cambiar,
        centros_disponibles=None,
        cargos_disponibles=None,
        especialidades_disponibles=None,
        dependencias_disponibles=None
    ):
        super().__init__(
            parent,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        self.icono_buscar = obtener_icono(
            "buscar",
            18
        )

        self.al_cambiar = al_cambiar
        self.combos = {}

        self._crear_buscador()

        self._crear_filtros(
            centros_disponibles=centros_disponibles or [],
            cargos_disponibles=cargos_disponibles or [],
            especialidades_disponibles=especialidades_disponibles or [],
            dependencias_disponibles=dependencias_disponibles or []
        )

    # ========================================================
    # BUSCADOR
    # ========================================================

    def _crear_buscador(self):

        contenedor = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        contenedor.pack(
            fill="x",
            padx=18,
            pady=(18, 12)
        )

        buscador_frame = tk.Frame(
            contenedor,
            bg="#F8FAFC",
            highlightbackground="#E2E8F0",
            highlightthickness=1
        )

        buscador_frame.pack(
            anchor="w",
            fill="x",
            ipadx=8,
            ipady=6
        )

        icono = tk.Label(
            buscador_frame,
            image=self.icono_buscar,
            bg="#F8FAFC"
        )

        icono.pack(
            side="left",
            padx=(12, 8)
        )

        self.entrada_busqueda = tk.Entry(
            buscador_frame,
            font=("Segoe UI", 11),
            fg="#94A3B8",
            bg="#FFFFFF",
            relief="flat",
            bd=0,
            insertbackground=COLOR_TEXTO
        )

        self.entrada_busqueda.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=6,
            padx=(0, 12)
        )

        self.entrada_busqueda.insert(
            0,
            PLACEHOLDER_BUSQUEDA
        )

        self.entrada_busqueda.bind(
            "<FocusIn>",
            self._limpiar_placeholder
        )

        self.entrada_busqueda.bind(
            "<FocusOut>",
            self._restaurar_placeholder
        )

        self.entrada_busqueda.bind(
            "<KeyRelease>",
            lambda event: self.al_cambiar()
        )

    def _restaurar_placeholder(self, event):

        if not self.entrada_busqueda.get().strip():

            self.entrada_busqueda.insert(
                0,
                PLACEHOLDER_BUSQUEDA
            )

            self.entrada_busqueda.config(
                fg="#94A3B8"
            )

    def _limpiar_placeholder(self, event):

        if self.entrada_busqueda.get() == PLACEHOLDER_BUSQUEDA:

            self.entrada_busqueda.delete(
                0,
                tk.END
            )

            self.entrada_busqueda.config(
                fg=COLOR_TEXTO
            )

    def obtener_texto_busqueda(self):

        texto = self.entrada_busqueda.get().strip()

        if texto.lower() == PLACEHOLDER_BUSQUEDA.lower():
            return ""

        return texto

    # ========================================================
    # FILTROS
    # ========================================================
    def _crear_filtros(
        self,
        centros_disponibles,
        cargos_disponibles,
        especialidades_disponibles,
        dependencias_disponibles
    ):

        filtros = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        filtros.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        definicion_filtros = [

            (
                "dependencia",
                "Dependencia",
                self._preparar_opciones(
                    dependencias_disponibles,
                    "Todas"
                )
            ),

            (
                "cargo",
                "Cargo",
                self._preparar_opciones(
                    cargos_disponibles,
                    "Todos"
                )
            ),
            
            (
                "especialidad",
                "Especialistas",
                self._preparar_opciones(
                    especialidades_disponibles,
                    "Todas"
                )
            ),

            (
                "centro",
                "Centro de salud",
                self._preparar_opciones(
                    centros_disponibles,
                    "Todos"
                )
            ),

            (
                "estatus",
                "Estatus",
                [
                    "Todos",
                    "Activo",
                    "Inactivo"
                ]
            )
        ]

        for columna, (clave, titulo, opciones) in enumerate(
            definicion_filtros
        ):

            self._crear_filtro(
                filtros,
                clave,
                titulo,
                opciones,
                columna
            )

    @staticmethod
    def _preparar_opciones(opciones, opcion_todos):

        """
        Limpia opciones dinámicas:

        - Elimina None.
        - Elimina cadenas vacías.
        - Elimina espacios innecesarios.
        - Elimina repetidos.
        - Ordena alfabéticamente.
        - Coloca "Todos" al principio solamente si existen
          valores reales.
        """

        valores = set()

        for opcion in opciones or []:

            if opcion is None:
                continue

            valor = str(opcion).strip()

            if not valor:
                continue

            if valor.lower() in (
                "todos",
                "todas"
            ):
                continue

            valores.add(valor)

        valores_ordenados = sorted(
            valores,
            key=lambda x: x.lower()
        )

        # Si no existe ningún valor real, no agregamos
        # "Todos" ni una opción vacía.
        if not valores_ordenados:
            return []

        return [
            opcion_todos,
            *valores_ordenados
        ]

    def _crear_filtro(
        self,
        parent,
        clave,
        titulo,
        opciones,
        columna
    ):

        frame = tk.Frame(
            parent,
            bg=COLOR_BLANCO
        )

        frame.grid(
            row=0,
            column=columna,
            sticky="ew",
            padx=5
        )

        parent.grid_columnconfigure(
            columna,
            weight=1
        )

        label = tk.Label(
            frame,
            text=titulo,
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO
        )

        label.pack(
            anchor="w",
            pady=(0, 5)
        )

        combo = ttk.Combobox(
            frame,
            values=opciones,
            state="readonly" if opciones else "disabled",
            font=("Segoe UI", 9)
        )

        if opciones:
            combo.current(0)

        combo.pack(
            fill="x",
            ipady=4
        )

        combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.al_cambiar()
        )

        self.combos[clave] = combo

    # ========================================================
    # ACTUALIZAR FILTROS DINÁMICAMENTE
    # ========================================================

    def actualizar_opciones(
        self,
        clave,
        opciones,
        opcion_todos="Todos"
    ):

        """
        Actualiza las opciones de un filtro dinámico.

        Se utiliza principalmente para:
            - Cargo
            - Centro de salud
        """

        combo = self.combos.get(clave)

        if not combo:
            return

        opciones_limpias = self._preparar_opciones(
            opciones,
            opcion_todos
        )

        combo["values"] = opciones_limpias

        if opciones_limpias:

            combo.configure(
                state="readonly"
            )

            combo.current(0)

        else:

            combo.set("")

            combo.configure(
                state="disabled"
            )

    def actualizar_cargos(self, cargos):

        self.actualizar_opciones(
            "cargo",
            cargos,
            "Todos"
        )

    def actualizar_centros(self, centros):

        self.actualizar_opciones(
            "centro",
            centros,
            "Todos"
        )

    def actualizar_especialidades(self, especialidades):

        self.actualizar_opciones(
            "especialidad",
            especialidades,
            "Todas"
        )
    # ========================================================
    # OBTENER FILTROS
    # ========================================================

    def obtener_filtros(self):

        return {
            clave: combo.get().strip()
            for clave, combo in self.combos.items()
        }
        
    def actualizar_dependencias(self, dependencias):

        self.actualizar_opciones(
            "dependencia",
            dependencias,
            "Todas"
        )
        
    def establecer_filtro(self, clave, valor):
        combo = self.combos.get(clave)

        if not combo:
            return

        valores = combo["values"]

        if valor in valores:
            combo.set(valor)