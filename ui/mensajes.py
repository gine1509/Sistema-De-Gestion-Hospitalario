import tkinter as tk
import customtkinter as ctk

from .Modulos.Medicos.colores import (
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
    COLOR_VERDE,
    COLOR_ROJO,
    COLOR_BORDE
)


class VentanaMensaje(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        tipo,
        titulo,
        mensaje
    ):
        super().__init__(parent)

        self.parent = parent
        self.tipo = tipo
        self.resultado = False

        # =====================================================
        # CONFIGURACIÓN DE LA VENTANA
        # =====================================================

        self.title(titulo)
        self.geometry("460x250")
        self.resizable(False, False)

        self.configure(
            fg_color=COLOR_BLANCO
        )

        # Mantener encima de la ventana principal
        self.transient(parent)
        self.grab_set()

        # Evitar que se cierre accidentalmente
        self.protocol(
            "WM_DELETE_WINDOW",
            self.cancelar
        )

        self._centrar_ventana()

        # =====================================================
        # CONFIGURAR COLORES SEGÚN EL TIPO
        # =====================================================

        configuracion = {

            "exito": {
                "color": COLOR_VERDE,
                "icono": "✓"
            },

            "error": {
                "color": COLOR_ROJO,
                "icono": "✕"
            },

            "advertencia": {
                "color": "#F59E0B",
                "icono": "!"
            },

            "pregunta": {
                "color": COLOR_AZUL,
                "icono": "?"
            }
        }

        config = configuracion.get(
            tipo,
            configuracion["pregunta"]
        )

        color = config["color"]
        icono = config["icono"]

        # =====================================================
        # CONTENEDOR PRINCIPAL
        # =====================================================

        contenedor = ctk.CTkFrame(
            self,
            fg_color=COLOR_BLANCO
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

        # =====================================================
        # ICONO
        # =====================================================

        icono_frame = ctk.CTkFrame(
            contenedor,
            width=58,
            height=58,
            corner_radius=29,
            fg_color=color
        )

        icono_frame.pack(
            pady=(5, 12)
        )

        icono_frame.pack_propagate(False)

        etiqueta_icono = ctk.CTkLabel(
            icono_frame,
            text=icono,
            font=("Segoe UI", 28, "bold"),
            text_color=COLOR_BLANCO
        )

        etiqueta_icono.pack(
            expand=True
        )

        # =====================================================
        # TÍTULO
        # =====================================================

        etiqueta_titulo = ctk.CTkLabel(
            contenedor,
            text=titulo,
            font=("Segoe UI", 17, "bold"),
            text_color=COLOR_TEXTO
        )

        etiqueta_titulo.pack(
            pady=(0, 5)
        )

        # =====================================================
        # MENSAJE
        # =====================================================

        etiqueta_mensaje = ctk.CTkLabel(
            contenedor,
            text=mensaje,
            font=("Segoe UI", 12),
            text_color=COLOR_SECUNDARIO,
            wraplength=390,
            justify="center"
        )

        etiqueta_mensaje.pack(
            pady=(0, 18)
        )

        # =====================================================
        # BOTONES
        # =====================================================

        botones = ctk.CTkFrame(
            contenedor,
            fg_color="transparent"
        )

        botones.pack(
            fill="x"
        )

        if tipo == "pregunta":

            boton_cancelar = ctk.CTkButton(
                botones,
                text="Cancelar",
                width=120,
                height=38,
                corner_radius=8,
                fg_color=COLOR_BLANCO,
                hover_color="#F1F5F9",
                border_width=1,
                border_color=COLOR_BORDE,
                text_color=COLOR_TEXTO,
                font=("Segoe UI", 12, "bold"),
                command=self.cancelar
            )

            boton_cancelar.pack(
                side="left",
                padx=(35, 5)
            )

            boton_confirmar = ctk.CTkButton(
                botones,
                text="Confirmar",
                width=120,
                height=38,
                corner_radius=8,
                fg_color=COLOR_AZUL,
                hover_color=COLOR_AZUL_HOVER,
                text_color=COLOR_BLANCO,
                font=("Segoe UI", 12, "bold"),
                command=self.confirmar
            )

            boton_confirmar.pack(
                side="right",
                padx=(5, 35)
            )

        else:

            boton_aceptar = ctk.CTkButton(
                botones,
                text="Aceptar",
                width=130,
                height=38,
                corner_radius=8,
                fg_color=color,
                hover_color=self._color_hover(color),
                text_color=COLOR_BLANCO,
                font=("Segoe UI", 12, "bold"),
                command=self.confirmar
            )

            boton_aceptar.pack()

        # =====================================================
        # TECLA ENTER
        # =====================================================

        self.bind(
            "<Return>",
            lambda event: self.confirmar()
        )

        self.bind(
            "<Escape>",
            lambda event: self.cancelar()
        )

        self.focus_force()

    # =========================================================
    # CENTRAR VENTANA
    # =========================================================

    def _centrar_ventana(self):

        self.update_idletasks()

        ancho = 460
        alto = 250

        try:

            x = self.parent.winfo_rootx()
            y = self.parent.winfo_rooty()

            ancho_parent = self.parent.winfo_width()
            alto_parent = self.parent.winfo_height()

            x = x + (ancho_parent // 2) - (ancho // 2)
            y = y + (alto_parent // 2) - (alto // 2)

        except Exception:

            ancho_pantalla = self.winfo_screenwidth()
            alto_pantalla = self.winfo_screenheight()

            x = (ancho_pantalla // 2) - (ancho // 2)
            y = (alto_pantalla // 2) - (alto // 2)

        self.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

    # =========================================================
    # CONFIRMAR
    # =========================================================

    def confirmar(self):

        self.resultado = True

        self.destroy()

    # =========================================================
    # CANCELAR
    # =========================================================

    def cancelar(self):

        self.resultado = False

        self.destroy()

    # =========================================================
    # COLOR HOVER
    # =========================================================

    def _color_hover(self, color):

        colores = {
            COLOR_VERDE: "#15803D",
            COLOR_ROJO: "#B91C1C",
            "#F59E0B": "#D97706",
            COLOR_AZUL: COLOR_AZUL_HOVER
        }

        return colores.get(
            color,
            color
        )


# =============================================================
# FUNCIÓN GENERAL
# =============================================================

def mostrar_mensaje(
    parent,
    tipo,
    titulo,
    mensaje
):

    ventana = VentanaMensaje(
        parent,
        tipo,
        titulo,
        mensaje
    )

    parent.wait_window(
        ventana
    )

    return ventana.resultado


# =============================================================
# MENSAJE DE ÉXITO
# =============================================================

def mostrar_exito(
    parent,
    titulo="Operación exitosa",
    mensaje="La operación se realizó correctamente."
):

    return mostrar_mensaje(
        parent,
        "exito",
        titulo,
        mensaje
    )


# =============================================================
# MENSAJE DE ERROR
# =============================================================

def mostrar_error(
    parent,
    titulo="Error",
    mensaje="Ocurrió un error al realizar la operación."
):

    return mostrar_mensaje(
        parent,
        "error",
        titulo,
        mensaje
    )


# =============================================================
# MENSAJE DE ADVERTENCIA
# =============================================================

def mostrar_advertencia(
    parent,
    titulo="Advertencia",
    mensaje="Verifica la información antes de continuar."
):

    return mostrar_mensaje(
        parent,
        "advertencia",
        titulo,
        mensaje
    )


# =============================================================
# MENSAJE DE PREGUNTA
# =============================================================

def mostrar_pregunta(
    parent,
    titulo="Confirmar acción",
    mensaje="¿Deseas continuar?"
):

    return mostrar_mensaje(
        parent,
        "pregunta",
        titulo,
        mensaje
    )