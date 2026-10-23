import tkinter as tk
import customtkinter as ctk

from .colores import (
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_BORDE,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
    COLOR_VERDE,
    COLOR_ROJO
)

from ui.iconos import obtener_icono


class VentanaExportarMedicos(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        total_medicos,
        medicos_filtrados,
        filtros_aplicados,
        al_exportar
    ):
        super().__init__(parent)

        self.parent = parent
        self.total_medicos = total_medicos
        self.medicos_filtrados = medicos_filtrados
        self.filtros_aplicados = filtros_aplicados
        self.al_exportar = al_exportar

        self.seleccion = tk.StringVar(
            value="todos"
        )

        self.title("Exportar médicos")
        self.geometry("520x600")
        self.resizable(False, False)

        self.configure(
            fg_color=COLOR_BLANCO
        )

        self.transient(parent)
        self.grab_set()

        self._cargar_iconos()
        self._crear_interfaz()
        self._centrar()

    # ==========================================================
    # ICONOS
    # ==========================================================

    def _cargar_iconos(self):

        self.icono_pdf = obtener_icono(
            "guardar_pdf",
            42
        )

        self.icono_excel = obtener_icono(
            "guardar_excel",
            42
        )

    # ==========================================================
    # CENTRAR
    # ==========================================================

    def _centrar(self):

        self.update_idletasks()

        ancho = 520
        alto = 560

        x = (
            self.winfo_screenwidth() // 2
            - ancho // 2
        )

        y = (
            self.winfo_screenheight() // 2
            - alto // 2
        )

        self.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

    # ==========================================================
    # INTERFAZ
    # ==========================================================

    def _crear_interfaz(self):

        # ======================================================
        # CONTENEDOR PRINCIPAL
        # ======================================================

        contenedor = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_BLANCO,
            corner_radius=0
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # ======================================================
        # TÍTULO
        # ======================================================

        ctk.CTkLabel(
            contenedor,
            text="Exportar médicos",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_TEXTO
        ).pack(
            anchor="w"
        )

        ctk.CTkLabel(
            contenedor,
            text="Seleccione la información que desea exportar.",
            font=("Segoe UI", 11),
            text_color=COLOR_SECUNDARIO
        ).pack(
            anchor="w",
            pady=(4, 22)
        )

        # ======================================================
        # SECCIÓN ALCANCE
        # ======================================================

        ctk.CTkLabel(
            contenedor,
            text="¿Qué médicos desea exportar?",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_TEXTO
        ).pack(
            anchor="w",
            pady=(0, 10)
        )

        # ======================================================
        # OPCIÓN TODOS
        # ======================================================

        tarjeta_todos = ctk.CTkFrame(
            contenedor,
            fg_color="#F8FAFC",
            border_width=1,
            border_color=COLOR_BORDE,
            corner_radius=10
        )

        tarjeta_todos.pack(
            fill="x",
            pady=(0, 10)
        )

        radio_todos = ctk.CTkRadioButton(
            tarjeta_todos,
            text="Todos los médicos",
            variable=self.seleccion,
            value="todos",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,
            command=self._actualizar_estado
        )

        radio_todos.pack(
            anchor="w",
            padx=15,
            pady=(13, 2)
        )

        ctk.CTkLabel(
            tarjeta_todos,
            text=f"{self.total_medicos} médicos registrados",
            font=("Segoe UI", 13),
            text_color=COLOR_SECUNDARIO
        ).pack(
            anchor="w",
            padx=42,
            pady=(0, 13)
        )

        # ======================================================
        # OPCIÓN FILTRADOS
        # ======================================================

        tarjeta_filtrados = ctk.CTkFrame(
            contenedor,
            fg_color="#F8FAFC",
            border_width=1,
            border_color=COLOR_BORDE,
            corner_radius=10
        )

        tarjeta_filtrados.pack(
            fill="x",
            pady=(0, 10)
        )

        radio_filtrados = ctk.CTkRadioButton(
            tarjeta_filtrados,
            text="Médicos filtrados",
            variable=self.seleccion,
            value="filtrados",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,
            command=self._actualizar_estado
        )

        radio_filtrados.pack(
            anchor="w",
            padx=15,
            pady=(13, 2)
        )

        self.label_filtrados = ctk.CTkLabel(
            tarjeta_filtrados,
            text=f"{len(self.medicos_filtrados)} médicos encontrados",
            font=("Segoe UI", 13),
            text_color=COLOR_SECUNDARIO
        )

        self.label_filtrados.pack(
            anchor="w",
            padx=42,
            pady=(0, 10)
        )

        # ======================================================
        # FILTROS APLICADOS
        # ======================================================

        self.frame_filtros = ctk.CTkFrame(
            tarjeta_filtrados,
            fg_color="transparent"
        )

        self.frame_filtros.pack(
            fill="x",
            padx=42,
            pady=(0, 12)
        )

        self._mostrar_filtros()

        # ======================================================
        # SEPARADOR
        # ======================================================

        ctk.CTkFrame(
            contenedor,
            height=1,
            fg_color=COLOR_BORDE
        ).pack(
            fill="x",
            pady=(10, 18)
        )

        # ======================================================
        # FORMATO
        # ======================================================

        ctk.CTkLabel(
            contenedor,
            text="Seleccione el formato",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_TEXTO
        ).pack(
            anchor="w",
            pady=(0, 12)
        )

        # ======================================================
        # BOTONES DE EXPORTACIÓN
        # ======================================================

        botones = ctk.CTkFrame(
            contenedor,
            fg_color="transparent"
        )

        botones.pack(
            fill="x"
        )

        botones.grid_columnconfigure(
            0,
            weight=1
        )

        botones.grid_columnconfigure(
            1,
            weight=1
        )

        self.btn_pdf = ctk.CTkButton(
            botones,
            text="PDF",
            image=self.icono_pdf,
            compound="top",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_BLANCO,
            fg_color=COLOR_ROJO,
            hover_color="#B91C1C",
            corner_radius=10,
            cursor="hand2",
            height=105,
            command=lambda: self._exportar("pdf")
        )

        self.btn_pdf.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 7)
        )

        self.btn_excel = ctk.CTkButton(
            botones,
            text="Excel",
            image=self.icono_excel,
            compound="top",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_BLANCO,
            fg_color=COLOR_VERDE,
            hover_color="#15803D",
            corner_radius=10,
            cursor="hand2",
            height=105,
            command=lambda: self._exportar("excel")
        )

        self.btn_excel.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(7, 0)
        )

        

    # ==========================================================
    # MOSTRAR FILTROS
    # ==========================================================

    def _mostrar_filtros(self):

        for widget in self.frame_filtros.winfo_children():
            widget.destroy()

        filtros_validos = []

        for nombre, valor in self.filtros_aplicados.items():

            if valor is None:
                continue

            valor = str(valor).strip()

            if not valor:
                continue

            if valor.lower() in (
                "todos",
                "todas",
                "todos los médicos",
                "todas las dependencias"
            ):
                continue

            filtros_validos.append(
                f"{nombre}: {valor}"
            )

        if not filtros_validos:

            ctk.CTkLabel(
                self.frame_filtros,
                text="Sin filtros aplicados",
                font=("Segoe UI", 13),
                text_color=COLOR_SECUNDARIO
            ).pack(
                anchor="w"
            )

            return

        ctk.CTkLabel(
            self.frame_filtros,
            text="Filtros aplicados:",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_TEXTO
        ).pack(
            anchor="w",
            pady=(0, 3)
        )

        for filtro in filtros_validos:

            ctk.CTkLabel(
                self.frame_filtros,
                text=f"• {filtro}",
                font=("Segoe UI", 13),
                text_color=COLOR_SECUNDARIO
            ).pack(
                anchor="w"
            )

    # ==========================================================
    # ACTUALIZAR ESTADO
    # ==========================================================

    def _actualizar_estado(self):

        if self.seleccion.get() == "filtrados":

            if not self.medicos_filtrados:

                self.btn_pdf.configure(
                    state="disabled"
                )

                self.btn_excel.configure(
                    state="disabled"
                )

            else:

                self.btn_pdf.configure(
                    state="normal"
                )

                self.btn_excel.configure(
                    state="normal"
                )

        else:

            if self.total_medicos > 0:

                self.btn_pdf.configure(
                    state="normal"
                )

                self.btn_excel.configure(
                    state="normal"
                )

            else:

                self.btn_pdf.configure(
                    state="disabled"
                )

                self.btn_excel.configure(
                    state="disabled"
                )

    # ==========================================================
    # EXPORTAR
    # ==========================================================

    def _exportar(self, formato):

        alcance = self.seleccion.get()

        if alcance == "todos":

            medicos = self.parent.medicos

        else:

            medicos = self.medicos_filtrados

        self.al_exportar(
            formato,
            alcance,
            medicos,
            self.filtros_aplicados
        )

        self.destroy()

