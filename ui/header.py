import tkinter as tk
from datetime import datetime

# Importar función para iconos
from ui.iconos import obtener_icono


class Header(tk.Frame):

    def __init__(self, parent, usuario_actual=None):

        super().__init__(
            parent,
            bg="#0B4F94",
            height=70
        )

        self.pack_propagate(False)

        # ==========================================================
        # TÍTULO
        # ==========================================================

        titulo = tk.Label(
            self,
            text="Sistema de Gestión Hospitalaria",
            bg="#0B4F94",
            fg="white",
            font=("Segoe UI", 18, "bold")
        )

        titulo.pack(
            side="left",
            padx=20
        )

        # ==========================================================
        # FECHA
        # ==========================================================

        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre"
        }

        hoy = datetime.now()

        fecha_texto = (
            f"{hoy.day} de "
            f"{meses[hoy.month]} de "
            f"{hoy.year}"
        )

        # Contenedor de icono + fecha
        contenedor_fecha = tk.Frame(
            self,
            bg="#0B4F94"
        )

        contenedor_fecha.pack(
            side="right",
            padx=20
        )

        # Icono
        icono_fecha = obtener_icono("fecha", 22)

        if icono_fecha:

            label_icono_fecha = tk.Label(
                contenedor_fecha,
                image=icono_fecha,
                bg="#0B4F94"
            )

            label_icono_fecha.pack(
                side="left",
                padx=(0, 8)
            )

            # IMPORTANTE:
            # Mantener referencia de la imagen
            self.icono_fecha = icono_fecha

        # Fecha
        fecha = tk.Label(
            contenedor_fecha,
            text=fecha_texto,
            bg="#0B4F94",
            fg="white",
            font=("Segoe UI", 12, "bold")
        )

        fecha.pack(
            side="left"
        )

        # ==========================================================
        # USUARIO CONECTADO
        # ==========================================================

        if usuario_actual:

            rol_texto = "Administrador" if usuario_actual.get("rol") == "admin" else "Secretaria"
            texto_usuario = f"{usuario_actual.get('usuario', '')}  ·  {rol_texto}"

            contenedor_usuario = tk.Frame(
                self,
                bg="#0B4F94"
            )

            contenedor_usuario.pack(
                side="right",
                padx=(0, 10)
            )

            icono_usuario = obtener_icono("usuario", 20)

            if icono_usuario:
                label_icono_usuario = tk.Label(
                    contenedor_usuario,
                    image=icono_usuario,
                    bg="#0B4F94"
                )
                label_icono_usuario.pack(side="left", padx=(0, 6))
                self.icono_usuario = icono_usuario

            tk.Label(
                contenedor_usuario,
                text=texto_usuario,
                bg="#0B4F94",
                fg="white",
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")