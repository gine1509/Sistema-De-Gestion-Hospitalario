import tkinter as tk
import customtkinter as ctk

from .colores import (
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_BORDE,
    COLOR_AZUL,
    COLOR_AZUL_HOVER
)

from ui.iconos import obtener_icono


class TarjetaOficio(tk.Frame):
    """
    Tarjeta visual de un oficio.

    Muestra:
        - Número de oficio
        - Fecha
        - Destinatario
        - Botón Ver detalle siempre en la parte inferior
    """

    def __init__(
        self,
        parent,
        oficio,
        al_ver_detalle,
        al_editar=None,
        al_eliminar=None
    ):

        super().__init__(
            parent,
            bg=COLOR_BLANCO,
            highlightbackground="#D5DEE8",
            highlightthickness=1,
            width=350,
            height=225
        )

        # IMPORTANTE:
        # Mantiene todas las tarjetas con la misma altura.
        self.pack_propagate(False)

        self.oficio = oficio
        self.al_ver_detalle = al_ver_detalle
        self.al_editar = al_editar
        self.al_eliminar = al_eliminar

        # ====================================================
        # ICONOS
        # ====================================================

        self.icono_oficio = obtener_icono(
            "oficios",
            20
        )

        self.icono_fecha = obtener_icono(
            "calendario",
            14
        )

        self.icono_persona = obtener_icono(
            "persona",
            14
        )

        self.icono_ver = obtener_icono(
            "ver",
            16
        )

        self._crear_interfaz()

    # ========================================================
    # INTERFAZ
    # ========================================================

    def _crear_interfaz(self):

        # Primero creamos el PIE.
        #
        # Al usar side="bottom", esta zona siempre queda
        # pegada a la parte inferior de la tarjeta.

        self._crear_boton()

        # Después creamos el contenido superior.

        self._crear_encabezado()
        self._crear_fecha()
        self._crear_destinatario()

    # ========================================================
    # ENCABEZADO
    # ========================================================

    def _crear_encabezado(self):

        encabezado = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        encabezado.pack(
            fill="x",
            padx=18,
            pady=(17, 8)
        )

        # ----------------------------------------------------
        # ICONO
        # ----------------------------------------------------

        icono_fondo = tk.Frame(
            encabezado,
            bg=COLOR_AZUL,
            width=38,
            height=38
        )

        icono_fondo.pack(
            side="left"
        )

        icono_fondo.pack_propagate(False)

        if self.icono_oficio:

            tk.Label(
                icono_fondo,
                image=self.icono_oficio,
                bg=COLOR_AZUL
            ).place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

        # ----------------------------------------------------
        # NÚMERO
        # ----------------------------------------------------

        numero = self.oficio.get("numero")

        if not numero:
            numero = "Sin número"

        tk.Label(
            encabezado,
            text=f"Oficio N.º {numero}",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            anchor="w"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 0)
        )

    # ========================================================
    # FECHA
    # ========================================================

    def _crear_fecha(self):

        fila = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        fila.pack(
            fill="x",
            padx=18,
            pady=(2, 5)
        )

        if self.icono_fecha:

            tk.Label(
                fila,
                image=self.icono_fecha,
                bg=COLOR_BLANCO
            ).pack(
                side="left"
            )

        fecha = self.oficio.get("fecha")

        if fecha:

            try:
                fecha_texto = fecha.strftime(
                    "%d/%m/%Y"
                )

            except AttributeError:

                fecha_texto = str(fecha)

        else:

            fecha_texto = "Sin fecha"

        tk.Label(
            fila,
            text=fecha_texto,
            font=("Segoe UI", 9),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            anchor="w"
        ).pack(
            side="left",
            padx=(7, 0)
        )

    # ========================================================
    # DESTINATARIO
    # ========================================================

    def _crear_destinatario(self):

        fila = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        fila.pack(
            fill="x",
            padx=18,
            pady=(2, 0)
        )

        # ----------------------------------------------------
        # ICONO
        # ----------------------------------------------------

        if self.icono_persona:

            tk.Label(
                fila,
                image=self.icono_persona,
                bg=COLOR_BLANCO
            ).pack(
                side="left",
                anchor="n"
            )

        # ----------------------------------------------------
        # DESTINATARIO
        # ----------------------------------------------------

        destinatario = self.oficio.get(
            "destinatario"
        )

        if (
            not destinatario
            or not str(destinatario).strip()
        ):

            destinatario = "Sin destinatario"

        tk.Label(
            fila,
            text=destinatario,
            font=("Segoe UI", 9),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            anchor="w",
            justify="left",

            # Limitamos el texto para evitar que
            # una tarjeta crezca demasiado.
            wraplength=270,

        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(7, 0)
        )

    # ========================================================
    # BOTÓN / PIE FIJO
    # ========================================================

    def _crear_boton(self):

        # ====================================================
        # PIE
        # ====================================================
        #
        # ESTA ES LA PARTE IMPORTANTE.
        #
        # side="bottom" hace que el pie se coloque siempre
        # en la parte inferior de la tarjeta.
        #
        # Se crea ANTES que el contenido para reservar
        # físicamente ese espacio.
        # ====================================================

        pie = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        pie.pack(
            side="bottom",
            fill="x",
            padx=18,
            pady=(0, 14)
        )

        # ----------------------------------------------------
        # SEPARADOR
        # ----------------------------------------------------

        tk.Frame(
            pie,
            bg="#EEF2F7",
            height=1
        ).pack(
            fill="x",
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # BOTÓN
        # ----------------------------------------------------

        boton = ctk.CTkButton(
            pie,
            text="Ver detalle",
            image=self.icono_ver,
            compound="left",

            font=(
                "Segoe UI",
                12,
                "bold"
            ),

            text_color=COLOR_BLANCO,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,

            corner_radius=9,

            height=36,

            cursor="hand2",

            command=lambda: self.al_ver_detalle(
                self.oficio
            )
        )

        boton.pack(
            fill="x"
        )