import tkinter as tk
import customtkinter as ctk
import re

from datetime import datetime, date

from .colores import (
    COLOR_FONDO,
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
    COLOR_BORDE,
    COLOR_ROJO
)

from ui.iconos import obtener_icono

from services.oficio_service import (
    obtener_siguiente_numero,
    numero_ya_existe,
    crear_oficio,
    actualizar_oficio
)

from ui.mensajes import (
    mostrar_exito,
    mostrar_error
)


class VentanaFormularioOficio(ctk.CTkToplevel):

    def __init__(self, parent, al_guardar=None, oficio_editar=None):

        super().__init__(parent)

        self.al_guardar = al_guardar
        self.oficio_editar = oficio_editar

        self.title(
            "Editar oficio" if oficio_editar
            else "Agregar oficio"
        )

        self.geometry("820x650")
        self.resizable(False, False)

        self.configure(
            fg_color=COLOR_FONDO
        )

        self.transient(parent)
        self.grab_set()

        # =================================================
        # ICONOS
        # =================================================

        self.icono_oficio = obtener_icono(
            "oficios",
            28
        )

        self.icono_guardar = obtener_icono(
            "guardar",
            18
        )

        self.icono_cancelar = obtener_icono(
            "cancelar",
            18
        )

        # =================================================
        # INTERFAZ
        # =================================================

        self._crear_interfaz()

        # =================================================
        # DATOS INICIALES
        # =================================================

        if self.oficio_editar:
            self._cargar_datos_oficio()

        else:
            self.entry_numero.insert(
                0,
                str(obtener_siguiente_numero())
            )

            self.entry_fecha.insert(
                0,
                date.today().strftime("%d/%m/%Y")
            )

        self.after(
            10,
            self._centrar
        )

    # =====================================================
    # CENTRAR
    # =====================================================

    def _centrar(self):

        self.update_idletasks()

        ancho = 820
        alto = 650

        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        x = (pantalla_ancho - ancho) // 2
        y = (pantalla_alto - alto) // 2

        self.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

    # =====================================================
    # INTERFAZ
    # =====================================================

    def _crear_interfaz(self):

        self._crear_header()

        # -------------------------------------------------
        # SCROLL
        # -------------------------------------------------

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        scroll.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        # -------------------------------------------------
        # INFORMACIÓN DEL OFICIO
        # -------------------------------------------------

        tarjeta = self._crear_tarjeta(
            scroll,
            "Información del oficio"
        )

        tarjeta.grid_columnconfigure(
            0,
            weight=1
        )

        tarjeta.grid_columnconfigure(
            1,
            weight=1
        )

        # -------------------------------------------------
        # NÚMERO
        # -------------------------------------------------

        campo, self.entry_numero = self._campo(
            tarjeta,
            "N° de oficio *"
        )

        campo.grid(
            row=0,
            column=0,
            padx=(5, 5),
            pady=5,
            sticky="ew"
        )

        self.entry_numero.bind(
            "<KeyRelease>",
            self._validar_numero,
            add="+"
        )

        # -------------------------------------------------
        # FECHA
        # -------------------------------------------------

        campo, self.entry_fecha = self._campo(
            tarjeta,
            "Fecha *"
        )

        campo.grid(
            row=0,
            column=1,
            padx=(5, 5),
            pady=5,
            sticky="ew"
        )

        self.entry_fecha.configure(
            placeholder_text="DD/MM/AAAA"
        )

        self.entry_fecha.bind(
            "<KeyRelease>",
            self._validar_fecha,
            add="+"
        )

        # -------------------------------------------------
        # DESTINATARIO
        # -------------------------------------------------

        campo, self.entry_destinatario = self._campo_texto(
            tarjeta,
            "Destinatario *",
            alto=75
        )

        campo.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky="ew"
        )

        self.entry_destinatario.bind(
            "<KeyRelease>",
            lambda event: self._limpiar_error_texto(self.entry_destinatario),
            add="+"
        )

        # -------------------------------------------------
        # ASUNTO
        # -------------------------------------------------

        campo, self.entry_asunto = self._campo_texto(
            tarjeta,
            "Asunto *",
            alto=90
        )

        campo.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky="ew"
        )

        self.entry_asunto.bind(
            "<KeyRelease>",
            lambda event: self._limpiar_error_texto(self.entry_asunto),
            add="+"
        )

        # -------------------------------------------------
        # OBSERVACIÓN
        # -------------------------------------------------

        campo, self.entry_observacion = self._campo_texto(
            tarjeta,
            "Observación"
            ,
            alto=100
        )

        campo.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky="ew"
        )

        self.entry_observacion.bind(
            "<KeyRelease>",
            lambda event: self._limpiar_error_texto(self.entry_observacion),
            add="+"
        )

        # -------------------------------------------------
        # BOTONES
        # -------------------------------------------------

        self._crear_botones()

    # =====================================================
    # HEADER
    # =====================================================

    def _crear_header(self):

        header = tk.Frame(
            self,
            bg=COLOR_AZUL,
            height=90
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        fila = tk.Frame(
            header,
            bg=COLOR_AZUL
        )

        fila.pack(
            anchor="w",
            padx=25,
            pady=(15, 0)
        )

        if self.icono_oficio:

            tk.Label(
                fila,
                image=self.icono_oficio,
                bg=COLOR_AZUL
            ).pack(
                side="left",
                padx=(0, 8)
            )

        titulo = (
            "Editar oficio"
            if self.oficio_editar
            else "Agregar oficio"
        )

        tk.Label(
            fila,
            text=titulo,
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg=COLOR_AZUL
        ).pack(
            side="left"
        )

        tk.Label(
            header,
            text="Registro de correspondencia y oficios",
            font=("Segoe UI", 11),
            fg="#DCE8FF",
            bg=COLOR_AZUL
        ).pack(
            anchor="w",
            padx=25
        )

    # =====================================================
    # TARJETA
    # =====================================================

    def _crear_tarjeta(self, parent, titulo):

        tarjeta = tk.Frame(
            parent,
            bg=COLOR_BLANCO,
            highlightbackground="#CBD5E1",
            highlightthickness=2,
            padx=10,
            pady=10
        )

        tarjeta.pack(
            fill="x",
            pady=(0, 12)
        )

        tk.Label(
            tarjeta,
            text=titulo,
            font=("Segoe UI", 12, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 10)
        )

        contenido = tk.Frame(
            tarjeta,
            bg=COLOR_BLANCO
        )

        contenido.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        return contenido

    # =====================================================
    # CAMPO NORMAL
    # =====================================================

    def _campo(self, parent, texto):

        frame = tk.Frame(
            parent,
            bg=COLOR_BLANCO
        )

        tk.Label(
            frame,
            text=texto,
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_BLANCO,
            fg=COLOR_TEXTO
        ).pack(
            anchor="w",
            pady=(0, 4)
        )

        entry = ctk.CTkEntry(
            frame,
            height=42,
            fg_color="#FFFFFF",
            border_color="#64748B",
            border_width=2,
            text_color="#0F172A",
            placeholder_text_color="#64748B",
            corner_radius=8
        )

        entry.pack(
            fill="x"
        )

        label_error = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 9),
            fg="#DC2626",
            bg=COLOR_BLANCO
        )

        label_error.pack(
            anchor="w",
            pady=(3, 0)
        )

        entry.label_error = label_error

        return frame, entry

    # =====================================================
    # CAMPO DE TEXTO
    # =====================================================

    def _campo_texto(
        self,
        parent,
        texto,
        alto=80
    ):

        frame = tk.Frame(
            parent,
            bg=COLOR_BLANCO
        )

        tk.Label(
            frame,
            text=texto,
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_BLANCO,
            fg=COLOR_TEXTO
        ).pack(
            anchor="w",
            pady=(0, 4)
        )

        textbox = ctk.CTkTextbox(
            frame,
            height=alto,
            fg_color="#FFFFFF",
            border_color="#64748B",
            border_width=2,
            text_color="#0F172A",
            corner_radius=8,
            font=("Segoe UI", 12)
        )

        textbox.pack(
            fill="x"
        )

        label_error = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 9),
            fg="#DC2626",
            bg=COLOR_BLANCO
        )

        label_error.pack(
            anchor="w",
            pady=(3, 0)
        )

        textbox.label_error = label_error

        return frame, textbox

    # =====================================================
    # VALIDACIÓN VISUAL
    # =====================================================

    def _error_entry(
        self,
        entry,
        mensaje
    ):

        entry.configure(
            border_color="#DC2626"
        )

        if hasattr(entry, "label_error"):

            entry.label_error.configure(
                text=mensaje
            )

    # =====================================================

    def _normal_entry(self, entry):

        entry.configure(
            border_color="#64748B"
        )

        if hasattr(entry, "label_error"):

            entry.label_error.configure(
                text=""
            )

    # =====================================================
    # CARGAR DATOS
    # =====================================================

    def _cargar_datos_oficio(self):

        oficio = self.oficio_editar

        # -------------------------------------------------
        # NÚMERO
        # -------------------------------------------------

        if hasattr(oficio, "numero"):

            self.entry_numero.insert(
                0,
                str(oficio.numero or "")
            )

        elif isinstance(oficio, dict):

            self.entry_numero.insert(
                0,
                str(oficio.get("numero", ""))
            )

        # -------------------------------------------------
        # FECHA
        # -------------------------------------------------

        fecha = None

        if hasattr(oficio, "fecha"):
            fecha = oficio.fecha

        elif isinstance(oficio, dict):
            fecha = oficio.get("fecha")

        if fecha:

            if isinstance(
                fecha,
                (datetime, date)
            ):

                fecha = fecha.strftime(
                    "%d/%m/%Y"
                )

            elif isinstance(fecha, str):

                try:

                    fecha = datetime.strptime(
                        fecha[:10],
                        "%Y-%m-%d"
                    ).strftime(
                        "%d/%m/%Y"
                    )

                except ValueError:
                    pass

            self.entry_fecha.insert(
                0,
                str(fecha)
            )

        # -------------------------------------------------
        # DESTINATARIO
        # -------------------------------------------------

        destinatario = ""

        if hasattr(oficio, "destinatario"):
            destinatario = oficio.destinatario or ""

        elif isinstance(oficio, dict):
            destinatario = oficio.get(
                "destinatario",
                ""
            ) or ""

        self.entry_destinatario.insert(
            "1.0",
            destinatario
        )

        # -------------------------------------------------
        # ASUNTO
        # -------------------------------------------------

        asunto = ""

        if hasattr(oficio, "asunto"):
            asunto = oficio.asunto or ""

        elif isinstance(oficio, dict):
            asunto = oficio.get(
                "asunto",
                ""
            ) or ""

        self.entry_asunto.insert(
            "1.0",
            asunto
        )

        # -------------------------------------------------
        # OBSERVACIÓN
        # -------------------------------------------------

        observacion = ""

        if hasattr(oficio, "observacion"):
            observacion = oficio.observacion or ""

        elif isinstance(oficio, dict):
            observacion = oficio.get(
                "observacion",
                ""
            ) or ""

        self.entry_observacion.insert(
            "1.0",
            observacion
        )

    # =====================================================
    # VALIDACIONES EN TIEMPO REAL
    # =====================================================

    def _validar_numero(self, event=None):

        valor = self.entry_numero.get()

        # Solo números
        numeros = "".join(
            c for c in valor
            if c.isdigit()
        )

        self.entry_numero.delete(
            0,
            "end"
        )

        self.entry_numero.insert(
            0,
            numeros
        )

        if numeros:
            self._normal_entry(
                self.entry_numero
            )

    # =====================================================

    def _validar_fecha(self, event=None):

        valor = self.entry_fecha.get()

        numeros = "".join(
            c for c in valor
            if c.isdigit()
        )[:8]

        dia = numeros[0:2]
        mes = numeros[2:4]
        anio = numeros[4:8]

        # -------------------------------------------------
        # DÍA
        # -------------------------------------------------

        if len(dia) == 2:

            d = int(dia)

            if d < 1:
                dia = "01"

            elif d > 31:
                dia = "31"

        # -------------------------------------------------
        # MES
        # -------------------------------------------------

        if len(mes) == 2:

            m = int(mes)

            if m < 1:
                mes = "01"

            elif m > 12:
                mes = "12"

        # -------------------------------------------------
        # AÑO
        # -------------------------------------------------

        if len(anio) == 4:

            a = int(anio)

            anio_actual = datetime.now().year

            if a < 1950:
                anio = "1950"

            elif a > anio_actual:
                anio = str(anio_actual)

        # -------------------------------------------------
        # FORMATO
        # -------------------------------------------------

        formateado = dia

        if mes:
            formateado += "/" + mes

        if anio:
            formateado += "/" + anio

        self.entry_fecha.delete(
            0,
            "end"
        )

        self.entry_fecha.insert(
            0,
            formateado
        )

        # Si ya está completa y es válida,
        # quitamos el error visual.

        if len(formateado) == 10:

            if self._fecha_valida(formateado):

                self._normal_entry(
                    self.entry_fecha
                )

    # =====================================================
    # FECHA VÁLIDA
    # =====================================================

    def _fecha_valida(self, valor):

        if not re.match(
            r"^\d{2}/\d{2}/\d{4}$",
            valor
        ):
            return False

        try:

            fecha = datetime.strptime(
                valor,
                "%d/%m/%Y"
            )

        except ValueError:

            return False

        anio_actual = datetime.now().year

        # No permitir años demasiado antiguos
        if fecha.year < 1950:
            return False

        # No permitir años futuros
        if fecha.year > anio_actual:
            return False

        # No permitir fechas futuras
        if fecha.date() > date.today():
            return False

        return True

    # =====================================================
    # LIMPIAR ERROR DE TEXTBOX
    # =====================================================

    def _limpiar_error_texto(self, widget):

        contenido = widget.get(
            "1.0",
            "end"
        ).strip()

        if contenido:

            self._normal_entry(
                widget
            )

    # =====================================================
    # BOTONES
    # =====================================================

    def _crear_botones(self):

        botones = tk.Frame(
            self,
            bg=COLOR_FONDO
        )

        botones.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        # -------------------------------------------------
        # CANCELAR
        # -------------------------------------------------

        btn_cancelar = ctk.CTkButton(
            botones,
            text="Cancelar",
            image=self.icono_cancelar,
            compound="left",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color="#6C757D",
            hover_color="#4B5563",
            corner_radius=10,
            cursor="hand2",
            height=44,
            width=160,
            command=self.destroy
        )

        btn_cancelar.pack(
            side="left"
        )

        # -------------------------------------------------
        # GUARDAR
        # -------------------------------------------------

        texto_btn = (
            "Actualizar oficio"
            if self.oficio_editar
            else "Guardar oficio"
        )

        btn_guardar = ctk.CTkButton(
            botones,
            text=texto_btn,
            image=self.icono_guardar,
            compound="left",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=COLOR_AZUL_HOVER,
            hover_color=COLOR_AZUL,
            corner_radius=10,
            cursor="hand2",
            height=44,
            width=190,
            command=self.guardar
        )

        btn_guardar.pack(
            side="right"
        )

    # =====================================================
    # VALIDAR Y GUARDAR
    # =====================================================

    def guardar(self):

        # =================================================
        # LIMPIAR ERRORES ANTERIORES
        # =================================================

        self._normal_entry(
            self.entry_numero
        )

        self._normal_entry(
            self.entry_fecha
        )

        self._normal_entry(
            self.entry_destinatario
        )

        self._normal_entry(
            self.entry_asunto
        )

        self._normal_entry(
            self.entry_observacion
        )

        # =================================================
        # OBTENER DATOS
        # =================================================

        numero = self.entry_numero.get().strip()

        fecha_texto = self.entry_fecha.get().strip()

        destinatario = self.entry_destinatario.get(
            "1.0",
            "end"
        ).strip()

        asunto = self.entry_asunto.get(
            "1.0",
            "end"
        ).strip()

        observacion = self.entry_observacion.get(
            "1.0",
            "end"
        ).strip()

        hay_error = False

        # =================================================
        # NÚMERO
        # =================================================

        if not numero:

            self._error_entry(
                self.entry_numero,
                "El número de oficio es obligatorio."
            )

            hay_error = True

        # =================================================
        # FECHA
        # =================================================

        if not fecha_texto:

            self._error_entry(
                self.entry_fecha,
                "La fecha es obligatoria."
            )

            hay_error = True

        elif not self._fecha_valida(
            fecha_texto
        ):

            self._error_entry(
                self.entry_fecha,
                "La fecha no es válida. Usa DD/MM/AAAA."
            )

            hay_error = True

        # =================================================
        # DESTINATARIO
        # =================================================

        if not destinatario:

            self._error_entry(
                self.entry_destinatario,
                "El destinatario es obligatorio."
            )

            hay_error = True

        # =================================================
        # ASUNTO
        # =================================================

        if not asunto:

            self._error_entry(
                self.entry_asunto,
                "El asunto es obligatorio."
            )

            hay_error = True

        # =================================================
        # NÚMERO DUPLICADO
        # =================================================

        id_actual = None

        if self.oficio_editar:
            if hasattr(self.oficio_editar, "id_oficio"):
                id_actual = self.oficio_editar.id_oficio
            elif isinstance(self.oficio_editar, dict):
                id_actual = self.oficio_editar.get("id_oficio")

        # Obtener el año de la fecha que está escribiendo
        anio_oficio = None
        if fecha_texto and self._fecha_valida(fecha_texto):
            anio_oficio = datetime.strptime(fecha_texto, "%d/%m/%Y").year

        if numero and numero_ya_existe(numero, id_actual, anio=anio_oficio):
            self._error_entry(
                self.entry_numero,
                f"Ya existe un oficio registrado con el número {numero} en este año."
            )
            hay_error = True

        # =================================================
        # SI HAY ERRORES, NO GUARDAR
        # =================================================

        if hay_error:
            return

        # =================================================
        # CONVERTIR FECHA
        # =================================================

        fecha_convertida = datetime.strptime(
            fecha_texto,
            "%d/%m/%Y"
        ).date()

        # =================================================
        # DATOS
        # =================================================

        datos = {
            "numero": numero,
            "fecha": fecha_convertida,
            "destinatario": destinatario,
            "asunto": asunto,
            "observacion": observacion
        }

        # =================================================
        # GUARDAR
        # =================================================

        try:

            if self.oficio_editar:

                resultado = actualizar_oficio(
                    self.oficio_editar.id_oficio,
                    datos
                )

                mostrar_exito(
                    self,
                    mensaje="El oficio se actualizó correctamente."
                )

            else:

                resultado = crear_oficio(
                    datos
                )

                mostrar_exito(
                    self,
                    mensaje="El oficio se registró correctamente."
                )

            # -------------------------------------------------
            # ACTUALIZAR LISTADO
            # -------------------------------------------------

            if self.al_guardar:
                self.al_guardar()

            self.destroy()

        except Exception as error:

            mostrar_error(
                self,
                mensaje=(
                    "No se pudo guardar el oficio.\n"
                    f"{error}"
                )
            )