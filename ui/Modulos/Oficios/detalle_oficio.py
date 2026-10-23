import tkinter as tk
import customtkinter as ctk
from ui.iconos import obtener_icono
from ui.sesion import es_admin

from .colores import (
    COLOR_FONDO,
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_BORDE,
    COLOR_AZUL,
    COLOR_AZUL_HOVER
)

from services.oficio_export_service import exportar_oficio_pdf


class VentanaDetalleOficio(tk.Toplevel):

    def __init__(
        self,
        parent,
        oficio,
        al_editar=None,
        al_eliminar=None
    ):
        super().__init__(parent)

        self.oficio = oficio
        self.al_editar = al_editar
        self.al_eliminar = al_eliminar

        self.title("Detalle del oficio")
        self.geometry("600x680")
        self.minsize(540, 600)

        self.configure(
            bg=COLOR_FONDO
        )

        self.transient(parent)
        self.grab_set()

        self._centrar_ventana()
        self._crear_interfaz()

    # ========================================================
    # CENTRAR
    # ========================================================

    def _centrar_ventana(self):

        self.update_idletasks()

        ancho = self.winfo_width()
        alto = self.winfo_height()

        padre_x = self.master.winfo_rootx()
        padre_y = self.master.winfo_rooty()

        padre_ancho = self.master.winfo_width()
        padre_alto = self.master.winfo_height()

        x = padre_x + (padre_ancho - ancho) // 2
        y = padre_y + (padre_alto - alto) // 2

        self.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

    # ========================================================
    # INTERFAZ
    # ========================================================

    def _crear_interfaz(self):
        
        self.icono_editar = obtener_icono(
            "editar_oficio",
            20
        )

        self.icono_eliminar = obtener_icono(
            "eliminar_oficio",
            20
        )
        
        self.icono_exportar = obtener_icono(
            "guardar_pdf",  
            20
        )

        # ====================================================
        # CONTENEDOR PRINCIPAL
        # ====================================================

        contenedor = tk.Frame(
            self,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=25
        )

        # ====================================================
        # ENCABEZADO AZUL
        # ====================================================

        encabezado = tk.Frame(
            contenedor,
            bg=COLOR_AZUL,
            height=105
        )

        encabezado.pack(
            fill="x"
        )

        encabezado.pack_propagate(False)

        # Contenido del encabezado
        info_encabezado = tk.Frame(
            encabezado,
            bg=COLOR_AZUL
        )

        info_encabezado.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        # Título
        tk.Label(
            info_encabezado,
            text="Detalle del oficio",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_BLANCO,
            bg=COLOR_AZUL,
            anchor="w"
        ).pack(
            fill="x"
        )

        # Número
        tk.Label(
            info_encabezado,
            text=f"Oficio N.º {self.oficio.numero}",
            font=("Segoe UI", 11, "bold"),
            fg="#E2E8F0",
            bg=COLOR_AZUL,
            anchor="w"
        ).pack(
            fill="x",
            pady=(4, 0)
        )

        # ====================================================
        # CONTENIDO
        # ====================================================

        contenido = tk.Frame(
            contenedor,
            bg=COLOR_BLANCO
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(22, 5)
        )

        # ----------------------------------------------------
        # FECHA
        # ----------------------------------------------------

        self._crear_campo(
            contenido,
            "Fecha",
            self._formatear_fecha(
                self.oficio.fecha
            )
        )

        # ----------------------------------------------------
        # DESTINATARIO
        # ----------------------------------------------------

        self._crear_campo(
            contenido,
            "Destinatario",
            self.oficio.destinatario
        )

        # ----------------------------------------------------
        # ASUNTO
        # ----------------------------------------------------

        self._crear_campo(
            contenido,
            "Asunto",
            self.oficio.asunto
        )

        # ----------------------------------------------------
        # OBSERVACIONES
        # ----------------------------------------------------

        observacion = self.oficio.observacion

        if observacion and str(observacion).strip():

            self._crear_campo(
                contenido,
                "Observaciones",
                observacion
            )

        # ====================================================
        # PIE DE BOTONES
        # ====================================================

        pie = tk.Frame(
            contenedor,
            bg=COLOR_BLANCO
        )

        pie.pack(
            fill="x",
            padx=25,
            pady=(15, 22)
        )

        # ----------------------------------------------------
        # ELIMINAR (solo administrador)
        # ----------------------------------------------------

        if es_admin():
            ctk.CTkButton(
                pie,
                text="Eliminar oficio",
                image=self.icono_eliminar,
                compound="left",
                width=145,
                height=38,
                corner_radius=8,
                fg_color="#DC2626",
                hover_color="#B91C1C",
                text_color=COLOR_BLANCO,
                font=("Segoe UI", 13, "bold"),
                command=self._ejecutar_eliminar
            ).pack(
                side="right",
                padx=(0, 10)
            )

        # ----------------------------------------------------
        # EDITAR
        # ----------------------------------------------------

        ctk.CTkButton(
            pie,
            text="Editar oficio",
            image=self.icono_editar,
            compound="left",
            width=135,
            height=38,
            corner_radius=8,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,
            text_color=COLOR_BLANCO,
            font=("Segoe UI", 13, "bold"),
            command=self._ejecutar_editar
        ).pack(
            side="right",
            padx=(0, 10)
        )

        # ----------------------------------------------------
        # EXPORTAR / DESCARGAR OFICIO
        # ----------------------------------------------------

        ctk.CTkButton(
            pie,
            text="Exportar oficio",
            image=self.icono_exportar,
            compound="left",
            width=150,
            height=38,
            corner_radius=8,
            fg_color="#0F766E",          # un verde azulado para diferenciarlo
            hover_color="#0D9488",
            text_color=COLOR_BLANCO,
            font=("Segoe UI", 13, "bold"),
            command=self._ejecutar_exportar
        ).pack(
            side="right",
            padx=(0, 10)
        )

        

    # ========================================================
    # CAMPO
    # ========================================================

    def _crear_campo(
        self,
        parent,
        titulo,
        valor
    ):

        if valor is None:
            valor = "-"

        if not str(valor).strip():
            valor = "-"

        bloque = tk.Frame(
            parent,
            bg=COLOR_BLANCO
        )

        bloque.pack(
            fill="x",
            pady=(0, 18)
        )

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        tk.Label(
            bloque,
            text=titulo,
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            anchor="w"
        ).pack(
            fill="x"
        )

        # ----------------------------------------------------
        # VALOR
        # ----------------------------------------------------

        tk.Label(
            bloque,
            text=str(valor),
            font=("Segoe UI", 11),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            anchor="w",
            justify="left",
            wraplength=470
        ).pack(
            fill="x",
            pady=(4, 0)
        )

    # ========================================================
    # EDITAR
    # ========================================================

    def _ejecutar_editar(self):

        if self.al_editar:

            self.destroy()

            self.al_editar(
                self.oficio
            )

    # ========================================================
    # ELIMINAR
    # ========================================================

    def _ejecutar_eliminar(self):

        if self.al_eliminar:

            self.al_eliminar(
                self.oficio
            )

    # ========================================================
    # FECHA
    # ========================================================

    def _formatear_fecha(self, fecha):

        if not fecha:
            return "-"

        try:
            return fecha.strftime("%d/%m/%Y")

        except AttributeError:
            return str(fecha)
        
    def _ejecutar_exportar(self):
        """
        Llama a la función de exportación PDF del oficio.
        """
        try:
            # Ajusta el import según dónde hayas colocado la función
            from services.oficio_export_service import exportar_oficio_pdf
            # o: from services.oficio_export_service import exportar_oficio_pdf
            # o desde el mismo módulo si está ahí

            exportar_oficio_pdf(self.oficio, parent_window=self)
        except Exception as e:
            from ui.mensajes import mostrar_error
            mostrar_error(
                self,
                "Error",
                f"No se pudo exportar el oficio:\n{str(e)}"
            )