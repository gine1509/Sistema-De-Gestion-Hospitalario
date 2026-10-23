import tkinter as tk

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
import customtkinter as ctk


class TarjetaMedico(tk.Frame):
    """
    Tarjeta de médico con la estructura:

        👤 Nombre                     ACTIVO
        V-27.327.640
        Médico Rural
        🏥 Hospital Padre Justo
        MPPS              Contratado
        📞 teléfono
        ✉  correo (solo si existe)
                    Ver perfil   ⋮
    """

    def __init__(
        self,
        parent,
        medico,
        al_ver_perfil,
        al_editar=None,
        al_eliminar=None
    ):
        super().__init__(
            parent,
            bg=COLOR_BLANCO,
            highlightbackground="#D5DEE8",
            highlightthickness=1,
            width=350,
            height=260
        )

        self.pack_propagate(False)

        self.medico = medico
        self.al_ver_perfil = al_ver_perfil
        self.al_editar = al_editar
        self.al_eliminar = al_eliminar

        

        self._crear_encabezado()
        self._crear_cedula()
        self._crear_cargo()
        self._crear_centro()
        self._crear_dependencia_contratacion()
        self._crear_contacto()
        self._crear_pie()

    # ========================================================
    # 👤 NOMBRE + ESTATUS
    # ========================================================

    # ========================================================
    # 👤 NOMBRE + ESTATUS
    # ========================================================

    def _crear_encabezado(self):

        encabezado = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        encabezado.pack(
            fill="x",
            padx=18,
            pady=(17, 6)
        )

        # ====================================================
        # ICONO DEL MÉDICO
        # ====================================================

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

        self.icono_medico = obtener_icono(
            "medicos",
            20
        )

        if self.icono_medico:

            icono_label = tk.Label(
                icono_fondo,
                image=self.icono_medico,
                bg=COLOR_AZUL
            )

            icono_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

        # ====================================================
        # NOMBRE
        # ====================================================

        nombre = tk.Label(
            encabezado,
            text=self.medico["nombre"],
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            anchor="w",
            justify="left",
            wraplength=190
        )

        nombre.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 8)
        )

        # ====================================================
        # ESTATUS
        # ====================================================

        color_estado = (
            COLOR_VERDE
            if self.medico["estatus"] == "ACTIVO"
            else COLOR_ROJO
        )

        estado = tk.Label(
            encabezado,
            text=self.medico["estatus"].upper(),
            font=("Segoe UI", 8, "bold"),
            fg=color_estado,
            bg=COLOR_BLANCO
        )

        estado.pack(
            side="right",
            anchor="n"
        )

    # ========================================================
    # CÉDULA
    # ========================================================

    def _crear_cedula(self):

        cedula = tk.Label(
            self,
            text=self.medico["cedula"],
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            anchor="w"
        )

        cedula.pack(
            fill="x",
            padx=18
        )

    # ========================================================
    # CARGO
    # ========================================================

    def _crear_cargo(self):
        cargo_texto = self.medico.get("cargo")
        if not cargo_texto or not str(cargo_texto).strip():
            cargo_texto = "Cargo no especificado"

        cargo = tk.Label(
            self,
            text=cargo_texto,
            font=("Segoe UI", 9),
            fg=COLOR_TEXTO if self.medico.get("cargo") else COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            anchor="w"
        )

        cargo.pack(
            fill="x",
            padx=18,
            pady=(4, 0)
        )

    # ========================================================
    # 🏥 CENTRO DE SALUD
    # ========================================================

    def _crear_centro(self):
        fila = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        fila.pack(
            fill="x",
            padx=18,
            pady=(2, 0)
        )

        self.icono_hospital = obtener_icono(
            "hospital",
            14
        )

        if self.icono_hospital:
            tk.Label(
                fila,
                image=self.icono_hospital,
                bg=COLOR_BLANCO
            ).pack(
                side="left"
            )

        centro_texto = self.medico.get("centro")
        if not centro_texto or not str(centro_texto).strip():
            centro_texto = "Centro no asignado"

        centro = tk.Label(
            fila,
            text=centro_texto,
            font=("Segoe UI", 9),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            anchor="w"
        )

        centro.pack(
            side="left",
            padx=(0, 0)
        )

    # ========================================================
    # DEPENDENCIA · CONTRATACIÓN
    # ========================================================

    def _crear_dependencia_contratacion(self):
        fila = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        fila.pack(
            fill="x",
            padx=18,
            pady=(10, 0)
        )

        dep_texto = self.medico.get("dependencia")
        if not dep_texto or not str(dep_texto).strip():
            dep_texto = "Sin dep."

        dependencia = tk.Label(
            fila,
            text=dep_texto,
            font=("Segoe UI", 8, "bold"),
            bg="#EFF6FF",
            fg=COLOR_AZUL,
            padx=6,
            pady=3
        )

        dependencia.pack(
            side="left"
        )

        cont_texto = self.medico.get("contratacion")
        if not cont_texto or not str(cont_texto).strip():
            cont_texto = "Sin contrato"

        etiqueta_contratacion = tk.Label(
            fila,
            text=cont_texto,
            font=("Segoe UI", 8, "bold"),
            bg="#F1F5F9",
            fg=COLOR_TEXTO,
            padx=8,
            pady=3
        )

        etiqueta_contratacion.pack(
            side="right"
        )

        # ----------------------------------------------------
        # TIPO DE CONTRATACIÓN
        # ----------------------------------------------------

       

        

    # ========================================================
    # 📞 ✉ CONTACTO
    # ========================================================

    def _crear_contacto(self):

        contacto = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        contacto.pack(
            fill="x",
            padx=18,
            pady=(12, 12)
        )

        fila = tk.Frame(
            contacto,
            bg=COLOR_BLANCO
        )

        fila.pack(
            fill="x"
        )

        self.icono_telefono = obtener_icono(
            "telefono",
            14
        )

        if self.icono_telefono:

            tk.Label(
                fila,
                image=self.icono_telefono,
                bg=COLOR_BLANCO
            ).pack(
                side="left"
            )

        telefono = self.medico.get("telefono")

        if not telefono or str(telefono).strip() == "":
            telefono = "No registrado"

        tk.Label(
            fila,
            text=telefono,
            font=("Segoe UI", 8),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            anchor="w"
        ).pack(
            side="left"
        )
        
        separador = tk.Frame(
            self,
            bg="#EEF2F7",
            height=1
        )

        separador.pack(
            fill="x",
            padx=18,
            pady=(0, 12)
        )

    # ========================================================
    # PIE: "Ver perfil"  ⋮
    # ========================================================

    def _crear_pie(self):

        pie = tk.Frame(
            self,
            bg=COLOR_BLANCO
        )

        pie.pack(
            fill="x",
            padx=18,
            pady=(0, 15)
        )

        self.icono_ver = obtener_icono(
            "ver",
            16
        )

        boton_perfil = ctk.CTkButton(
            pie,
            text="Ver perfil",
            image=self.icono_ver,
            compound="left",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_BLANCO,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,
            corner_radius=10,
            cursor="hand2",
            height=38,
            command=lambda: self.al_ver_perfil(
                self.medico
            )
        )

        boton_perfil.pack(
            fill="x"
        )