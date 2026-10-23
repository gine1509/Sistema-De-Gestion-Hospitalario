import tkinter as tk
import customtkinter as ctk
import re
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import unicodedata

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

from services.medico_service import (
    listar_dependencias,
    listar_tipos_contratacion,
    listar_estatus,
    crear_medico,
    actualizar_medico,
    buscar_por_cedula
)

from ui.mensajes import (
    mostrar_exito,
    mostrar_error
)


class VentanaFormularioMedico(ctk.CTkToplevel):

    def __init__(self, parent, al_guardar=None, medico_editar=None):

        super().__init__(parent)
        self.al_guardar = al_guardar
        self.medico_editar = medico_editar

        self.title("Editar médico" if medico_editar else "Agregar médico")
        self.geometry("820x650")
        self.resizable(False, False)

        self.configure(
            fg_color=COLOR_FONDO
        )

        self.transient(parent)
        self.grab_set()

        self.icono_medico = obtener_icono(
            "agregar_medico",
            28
        )
        
        self.dependencia_actual = None
        self.contratacion_actual = None
        self.estatus_actual = 1

        # Cargar catálogos desde la base de datos
        self.dependencias = listar_dependencias()
        self.contrataciones = listar_tipos_contratacion()
        self.estatus = listar_estatus()

        self.icono_guardar = obtener_icono(
            "guardar",
            18
        )

        self.icono_cancelar = obtener_icono(
            "cancelar",
            18
        )
        
        self.cargos_requieren_especialidad = {
                    "MEDICO ESPECIALISTA I",
                    "MEDICO ESPECIALISTA II",
                    "MEDICO ADJUNTO I",
                    "MEDICO ADJUNTO II",
                    "JEFE DE SERVICIO",
                    "MEDICO ESPECIALISTA",
                }

        self._crear_interfaz()
        
        if self.medico_editar:
            self._cargar_datos_medico()

        
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

        self._crear_personal(scroll)
        self._crear_profesional(scroll)
        self._crear_ubicacion(scroll)
        self._crear_formacion(scroll)
        self._crear_estado(scroll)

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

        if self.icono_medico:
            

            tk.Label(
                fila,
                image=self.icono_medico,
                bg=COLOR_AZUL
            ).pack(
                side="left",
                padx=(0, 8)
            )
        
        titulo = "Editar médico" if self.medico_editar else "Agregar médico"
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
            text="Registro de personal médico",
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
    # CAMPO
    # =====================================================

    def _campo(self, parent, texto):
        frame = tk.Frame(parent, bg=COLOR_BLANCO)
        tk.Label(frame, text=texto, font=("Segoe UI", 10, "bold"),
                bg=COLOR_BLANCO, fg=COLOR_TEXTO).pack(anchor="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            frame, height=42, fg_color="#FFFFFF",
            border_color="#64748B", border_width=2,
            text_color="#0F172A", placeholder_text_color="#64748B",
            corner_radius=8
        )
        entry.pack(fill="x")

        label_error = tk.Label(frame, text="", font=("Segoe UI", 9),
                                fg="#DC2626", bg=COLOR_BLANCO)
        label_error.pack(anchor="w", pady=(3, 0))
        entry.label_error = label_error

        # Usamos closure con "ent=entry" en vez de event.widget,
        # y add="+" para no pisar binds posteriores.
        entry.bind("<KeyRelease>", lambda e, ent=entry: self._normal_entry(ent), add="+")

        return frame, entry
    
    # =====================================================
    # ESTILOS VALIDACIÓN
    # =====================================================

    def _error_entry(self, entry, mensaje="La cédula es obligatoria."):

        entry.configure(
            border_color="#DC2626"
        )

        if hasattr(entry, "label_error"):
            entry.label_error.configure(
                text=mensaje
            )

    def _normal_entry(self, entry):

        entry.configure(
            border_color="#64748B"
        )

        if hasattr(entry, "label_error"):
            entry.label_error.configure(
                text=""
            )

    # =====================================================
    # PERSONAL
    # =====================================================

    def _crear_personal(self, parent):

        tarjeta = self._crear_tarjeta(
            parent,
            "Información personal"
        )

        tarjeta.grid_columnconfigure(0, weight=1)
        tarjeta.grid_columnconfigure(1, weight=1)
        
        campo, self.entry_cedula = self._campo(tarjeta, "Cédula *")
        campo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.entry_cedula.insert(0, "V-")
        self.entry_cedula.bind("<KeyRelease>", self._validar_cedula, add="+")
        
        campo, self.entry_codigo = self._campo(tarjeta, "Código")
        campo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_codigo.bind("<KeyRelease>", self._validar_codigo, add="+")
        
        campo, self.entry_nombres = self._campo(tarjeta, "Nombres *")
        campo.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.entry_nombres.bind("<KeyRelease>", self._validar_nombre, add="+")

        campo, self.entry_apellidos = self._campo(tarjeta, "Apellidos *")
        campo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_apellidos.bind("<KeyRelease>", self._validar_apellido, add="+")

        campo, self.entry_telefono = self._campo(tarjeta, "Teléfono")
        campo.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.entry_telefono.bind("<KeyRelease>", self._validar_telefono, add="+")

        campo, self.entry_correo = self._campo(tarjeta, "Correo")
        campo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.entry_correo.bind("<KeyRelease>", self._validar_correo, add="+")

    # =====================================================
    # PROFESIONAL
    # =====================================================

    def _crear_profesional(self, parent):

        tarjeta = self._crear_tarjeta(
            parent,
            "Información profesional"
        )

        tarjeta.grid_columnconfigure(0, weight=1)
        tarjeta.grid_columnconfigure(1, weight=1)
        
        campo, self.entry_fecha_ingreso = self._campo(
            tarjeta,
            "Fecha de ingreso"
        )
        campo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.entry_fecha_ingreso.configure(placeholder_text="DD/MM/AAAA")
        self.entry_fecha_ingreso.bind("<KeyRelease>", self._validar_fecha_ingreso, add="+")

        campo, self.entry_cargo = self._campo(tarjeta, "Cargo")
        campo.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        campo_esp, self.entry_especialidad = self._campo(tarjeta, "Especialidad")
        campo_esp.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Guardamos referencia al label para poder cambiar el texto dinámicamente
        self.label_especialidad = campo_esp.winfo_children()[0]

        # ... (todo el resto de dependencia y contratación se queda igual)

        self.entry_cargo.bind("<KeyRelease>", self._validar_mayusculas, add="+")
        self.entry_cargo.bind("<KeyRelease>", self._actualizar_estado_especialidad, add="+")
        self.entry_especialidad.bind("<KeyRelease>", self._validar_mayusculas, add="+")

        # Estado inicial (desactivado)
        self._actualizar_estado_especialidad()

        # DEPENDENCIA
        tk.Label(
            tarjeta, text="Dependencia", font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_BLANCO
        ).grid(row=2, column=0, sticky="w", padx=5)

        frame_dep = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        frame_dep.grid(row=3, column=0, padx=5, pady=(0, 10), sticky="ew")
        frame_dep.grid_columnconfigure(0, weight=1)
        frame_dep.grid_columnconfigure(1, weight=1)

        self.botones_dependencia = {}
        for columna, dependencia in enumerate(self.dependencias):
            boton = ctk.CTkButton(
                frame_dep,
                text=dependencia["nombre"],
                fg_color="#FFFFFF",
                text_color="#000000",
                border_width=2,
                border_color="#CBD5E1",
                command=lambda id_dep=dependencia["id_dependencia"]: self._toggle_dependencia(id_dep)
            )
            boton.grid(row=0, column=columna, padx=(0 if columna == 0 else 5, 5 if columna == 0 else 0), sticky="ew")
            self.botones_dependencia[dependencia["id_dependencia"]] = boton

        # CONTRATACIÓN
        tk.Label(
            tarjeta, text="Contratación", font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_BLANCO
        ).grid(row=2, column=1, sticky="w", padx=5)

        frame_cont = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        frame_cont.grid(row=3, column=1, padx=5, pady=(0, 10), sticky="ew")
        frame_cont.grid_columnconfigure(0, weight=1)
        frame_cont.grid_columnconfigure(1, weight=1)

        self.botones_contratacion = {}
        for columna, item in enumerate(self.contrataciones):
            boton = ctk.CTkButton(
                frame_cont,
                text=item["nombre"],
                fg_color="#FFFFFF",
                text_color="#000000",
                border_width=2,
                border_color="#CBD5E1",
                command=lambda id_tipo=item["id_tipo_contratacion"]: self._toggle_contratacion(id_tipo)
            )
            boton.grid(row=0, column=columna, padx=(0 if columna == 0 else 5, 5 if columna == 0 else 0), sticky="ew")
            self.botones_contratacion[item["id_tipo_contratacion"]] = boton
        
        

    
    # =====================================================
    # FORMACIÓN
    # =====================================================

    def _crear_formacion(self, parent):

        tarjeta = self._crear_tarjeta(
            parent,
            "Formación Académica en caso de estar estudiando"
        )

        campo, self.entry_formacion = self._campo(
            tarjeta,
            ""
        )
        campo.pack(fill="x")

        self.entry_formacion.configure(
            placeholder_text="Dejar en blanco si no se encuentra cursando ninguna formación académica"
        )

        tk.Label(
            tarjeta,
            text="Ejemplo: Especialización en Pediatría, Maestría en Salud Pública o Doctorado en Ciencias Médicas.",
            font=("Segoe UI", 9),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(8, 0))

        self.entry_formacion.bind("<KeyRelease>", self._validar_mayusculas, add="+")

    # =====================================================
    # UBICACIÓN
    # =====================================================

    def _crear_ubicacion(self, parent):

        tarjeta = self._crear_tarjeta(
            parent,
            "Ubicación laboral"
        )

        tarjeta.grid_columnconfigure(0, weight=1)
        tarjeta.grid_columnconfigure(1, weight=1)

        campo, self.entry_centro = self._campo(tarjeta, "Centro de salud")
        campo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        campo, self.entry_asic = self._campo(tarjeta, "ASIC")
        campo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        campo, self.entry_ubicacion = self._campo(tarjeta, "Ubicación administrativa")
        campo.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        campo, self.entry_tipologia = self._campo(tarjeta, "Tipología del centro")
        campo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.entry_centro.bind("<KeyRelease>", self._validar_mayusculas, add="+")
        self.entry_asic.bind("<KeyRelease>", self._validar_mayusculas, add="+")
        self.entry_ubicacion.bind("<KeyRelease>", self._validar_mayusculas, add="+")
        self.entry_tipologia.bind("<KeyRelease>", self._validar_mayusculas, add="+")

    # =====================================================
    # ESTADO
    # =====================================================

    def _crear_estado(self, parent):

        tarjeta = self._crear_tarjeta(
            parent,
            "Estado"
        )

        fila_estado = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        fila_estado.pack(anchor="w", pady=5)

        self.label_estado = tk.Label(
            fila_estado,
            text="Activo",
            font=("Segoe UI", 11, "bold"),
            fg="#16A34A",
            bg=COLOR_BLANCO
        )
        self.label_estado.pack(side="left", padx=(0, 10))

        self.switch_estado = ctk.CTkSwitch(
            fila_estado,
            text="",
            width=50,
            height=24,
            fg_color="#CBD5E1",
            progress_color="#16A34A",
            button_color="white",
            button_hover_color="#F8FAFC",
            command=self._cambio_estado
        )
        self.switch_estado.select()
        self.switch_estado.pack(side="left")

        self.frame_inactivo = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        
        campo, self.entry_causa = self._campo(
            self.frame_inactivo,
            "Causa de inactividad"
        )
        campo.pack(fill="x")

        self.entry_causa.configure(
            placeholder_text="Ejemplo: Jubilado, Reposo, Permiso, Renuncia o Comisión de servicio"
        )

        tk.Label(
            self.frame_inactivo,
            text="Complete este campo únicamente cuando el médico se encuentre inactivo.",
            font=("Segoe UI", 9),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(8, 0))

        self.entry_causa.bind("<KeyRelease>", self._validar_mayusculas, add="+")
        
        frame_fechas = tk.Frame(self.frame_inactivo, bg=COLOR_BLANCO)
        frame_fechas.pack(fill="x", pady=(10, 0))
        frame_fechas.grid_columnconfigure(0, weight=1)
        frame_fechas.grid_columnconfigure(1, weight=1)

        campo, self.entry_fecha_inicio_inactividad = self._campo(
            frame_fechas,
            "Fecha inicio de inactividad"
        )
        campo.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.entry_fecha_inicio_inactividad.configure(placeholder_text="DD/MM/AAAA")
        self.entry_fecha_inicio_inactividad.bind("<KeyRelease>", self._validar_fecha_inactividad, add="+")

        campo, self.entry_fecha_fin_inactividad = self._campo(
            frame_fechas,
            "Fecha fin de inactividad"
        )
        campo.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.entry_fecha_fin_inactividad.configure(placeholder_text="DD/MM/AAAA")
        self.entry_fecha_fin_inactividad.bind("<KeyRelease>", self._validar_fecha_inactividad, add="+")

        campo, self.entry_tiempo_inactividad = self._campo(
            self.frame_inactivo,
            "Tiempo de inactividad"
        )
        campo.pack(fill="x", pady=(10, 0))
        self.entry_tiempo_inactividad.configure(state="disabled")

    def _cambio_estado(self):

        if self.switch_estado.get():
            self.label_estado.configure(text="Activo", fg="#16A34A")
            self.frame_inactivo.pack_forget()
        else:
            self.label_estado.configure(text="Inactivo", fg="#DC2626")
            self.frame_inactivo.pack(fill="x", pady=10)
    
    def _cargar_datos_medico(self):
        m = self.medico_editar

        def _formatear_fecha_gui(val):
            if not val:
                return ""
            if isinstance(val, (datetime, date)):
                return val.strftime("%d/%m/%Y")
            if isinstance(val, str):
                # Si viene en formato ISO (YYYY-MM-DD)
                if re.match(r"^\d{4}-\d{2}-\d{2}", val):
                    try:
                        partes = val.split("-")
                        return f"{partes[2][:2]}/{partes[1]}/{partes[0]}"
                    except Exception:
                        pass
            return str(val)

        # Datos personales obligatorios y opcionales
        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, m.get("cedula", ""))
        
        if m.get("codigo"): self.entry_codigo.insert(0, m["codigo"])
        if m.get("nombres"): self.entry_nombres.insert(0, m["nombres"])
        if m.get("apellidos"): self.entry_apellidos.insert(0, m["apellidos"])
        if m.get("telefono"): self.entry_telefono.insert(0, m["telefono"])
        if m.get("correo"): self.entry_correo.insert(0, m["correo"])

        # Profesional
        if m.get("fecha_ingreso"):
            self.entry_fecha_ingreso.insert(0, _formatear_fecha_gui(m["fecha_ingreso"]))
            
        if m.get("cargo"):
            self.entry_cargo.insert(0, m["cargo"])
        if m.get("especialidad"):
            self.entry_especialidad.insert(0, m["especialidad"])

        # Aplicar la lógica de habilitar/deshabilitar
        self._actualizar_estado_especialidad()
        
        # Botones de selección múltiple (usamos los ID)
        if m.get("id_dependencia"): self._toggle_dependencia(m["id_dependencia"])
        if m.get("id_tipo_contratacion"): self._toggle_contratacion(m["id_tipo_contratacion"])

        # Ubicación y Formación
        if m.get("centro_salud"): self.entry_centro.insert(0, m["centro_salud"])
        if m.get("asic"): self.entry_asic.insert(0, m["asic"])
        if m.get("ubicacion_administrativa"): self.entry_ubicacion.insert(0, m["ubicacion_administrativa"])
        if m.get("tipologia_centro"): self.entry_tipologia.insert(0, m["tipologia_centro"])
        if m.get("formacion_estudiando"): self.entry_formacion.insert(0, m["formacion_estudiando"])

        # Estatus (Si está inactivo ID=2)
        if m.get("id_estatus") == 2:
            self.switch_estado.deselect()
            self._cambio_estado()

            if m.get("causa_inactividad"): self.entry_causa.insert(0, m["causa_inactividad"])
            
            if m.get("fecha_inicio_inactividad"):
                self.entry_fecha_inicio_inactividad.insert(0, _formatear_fecha_gui(m["fecha_inicio_inactividad"]))
            
            if m.get("fecha_fin_inactividad"):
                self.entry_fecha_fin_inactividad.insert(0, _formatear_fecha_gui(m["fecha_fin_inactividad"]))

            if m.get("tiempo_inactividad"):
                self.entry_tiempo_inactividad.configure(state="normal")
                self.entry_tiempo_inactividad.insert(0, m["tiempo_inactividad"])
                self.entry_tiempo_inactividad.configure(state="disabled")
            
    # =====================================================
    # VALIDACIONES
    # =====================================================
    
    def _validar_mayusculas(self, event):

        entry = event.widget
        valor = entry.get()
        cursor = entry.index("insert")

        entry.delete(0, "end")
        entry.insert(0, valor.upper())

        try:
            entry.icursor(cursor)
        except:
            pass

    def _validar_cedula(self, event=None):

        valor = self.entry_cedula.get()
        numeros = "".join(c for c in valor if c.isdigit())[:8]

        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, f"V-{numeros}")
    
    def _validar_nombre(self, event=None):

        valor = self.entry_nombres.get()
        limpio = "".join(c for c in valor if c.isalpha() or c.isspace()).upper()

        self.entry_nombres.delete(0, "end")
        self.entry_nombres.insert(0, limpio)
        
    def _validar_apellido(self, event=None):

        valor = self.entry_apellidos.get()
        limpio = "".join(c for c in valor if c.isalpha() or c.isspace()).upper()

        self.entry_apellidos.delete(0, "end")
        self.entry_apellidos.insert(0, limpio)
        
    def _validar_telefono(self, event=None):

        valor = self.entry_telefono.get()
        numeros = "".join(c for c in valor if c.isdigit())[:11]

        self.entry_telefono.delete(0, "end")
        self.entry_telefono.insert(0, numeros)
        
    def _validar_codigo(self, event=None):

        valor = self.entry_codigo.get()
        numeros = "".join(c for c in valor if c.isdigit())

        self.entry_codigo.delete(0, "end")
        self.entry_codigo.insert(0, numeros)
        
    def _validar_correo(self, event=None):
        valor = self.entry_correo.get().strip()
        if not valor or re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", valor):
            self._normal_entry(self.entry_correo)

    def _validar_fecha_ingreso(self, event=None):

        valor = self.entry_fecha_ingreso.get()
        numeros = "".join(c for c in valor if c.isdigit())[:8]

        dia = numeros[0:2]
        mes = numeros[2:4]
        anio = numeros[4:8]

        if len(dia) == 2:
            d = int(dia)
            if d < 1:
                dia = "01"
            elif d > 31:
                dia = "31"

        if len(mes) == 2:
            m = int(mes)
            if m < 1:
                mes = "01"
            elif m > 12:
                mes = "12"

        if len(anio) == 4:
            a = int(anio)
            anio_actual = datetime.now().year
            if a < 1950:
                anio = "1950"
            elif a > anio_actual:
                anio = str(anio_actual)

        formateado = dia
        if mes:
            formateado += "/" + mes
        if anio:
            formateado += "/" + anio

        self.entry_fecha_ingreso.delete(0, "end")
        self.entry_fecha_ingreso.insert(0, formateado)
        
    def _fecha_valida(self, valor):

        if not re.match(r"^\d{2}/\d{2}/\d{4}$", valor):
            return False

        try:
            fecha = datetime.strptime(valor, "%d/%m/%Y")
        except ValueError:
            return False

        anio_actual = datetime.now().year

        if fecha.year < 1950 or fecha.year > anio_actual:
            return False

        if fecha > datetime.now():
            return False

        return True


    def _seleccionar_dependencia(self, valor):

        if self.dependencia_actual == valor:
            self.dependencia_actual = None
            self.after(10, lambda: self.segment_dependencia.set(""))
        else:
            self.dependencia_actual = valor
            
    def _seleccionar_contratacion(self, valor):

        if self.contratacion_actual == valor:
            self.contratacion_actual = None
            self.after(10, lambda: self.segment_contratacion.set(""))
        else:
            self.contratacion_actual = valor
    
    def _toggle_dependencia(self, valor):

        if self.dependencia_actual == valor:
            self.dependencia_actual = None
        else:
            self.dependencia_actual = valor

        self._actualizar_dependencia()
        
    def _actualizar_dependencia(self):

        for boton in self.botones_dependencia.values():
            boton.configure(fg_color="#FFFFFF", text_color="#000000")

        if self.dependencia_actual is not None:
            boton = self.botones_dependencia.get(self.dependencia_actual)
            if boton:
                boton.configure(fg_color="#2563EB", text_color="white")

    def _toggle_contratacion(self, valor):

        if self.contratacion_actual == valor:
            self.contratacion_actual = None
        else:
            self.contratacion_actual = valor

        self._actualizar_contratacion()
        
    def _actualizar_contratacion(self):

        for boton in self.botones_contratacion.values():
            boton.configure(fg_color="#FFFFFF", text_color="#000000")

        if self.contratacion_actual is not None:
            boton = self.botones_contratacion.get(self.contratacion_actual)
            if boton:
                boton.configure(fg_color="#2563EB", text_color="white")
                
    def _obtener_id_estatus(self, nombre):

        nombre = nombre.upper()
        for item in self.estatus:
            if item["nombre"].upper() == nombre:
                return item["id_estatus"]
        return None
    
    def _formatear_fecha(self, entry):

        valor = entry.get()
        numeros = "".join(c for c in valor if c.isdigit())[:8]

        dia = numeros[:2]
        mes = numeros[2:4]
        anio = numeros[4:8]

        texto = dia
        if mes:
            texto += "/" + mes
        if anio:
            texto += "/" + anio

        entry.delete(0, "end")
        entry.insert(0, texto)
        
    def _actualizar_tiempo_inactividad(self, event=None):

        fecha_inicio = self.entry_fecha_inicio_inactividad.get().strip()
        fecha_fin = self.entry_fecha_fin_inactividad.get().strip()

        self.entry_tiempo_inactividad.configure(state="normal")
        self.entry_tiempo_inactividad.delete(0, "end")

        if not (
            self._fecha_inactividad_valida(fecha_inicio)
            and
            self._fecha_inactividad_valida(fecha_fin)
        ):
            self.entry_tiempo_inactividad.configure(state="disabled")
            return

        inicio = datetime.strptime(fecha_inicio, "%d/%m/%Y")
        fin = datetime.strptime(fecha_fin, "%d/%m/%Y")

        if fin < inicio:
            self.entry_tiempo_inactividad.insert(0, "Fechas inválidas")
            self.entry_tiempo_inactividad.configure(state="disabled")
            return

        diferencia = relativedelta(fin, inicio)

        anios = diferencia.years
        meses = diferencia.months
        dias = diferencia.days

        partes = []
        if anios:
            partes.append(f"{anios} año(s)")
        if meses:
            partes.append(f"{meses} mes(es)")
        if dias:
            partes.append(f"{dias} día(s)")

        if not partes:
            partes.append("0 días")

        self.entry_tiempo_inactividad.insert(0, ", ".join(partes))
        self.entry_tiempo_inactividad.configure(state="disabled")
        
    def _validar_fecha_generica(self, entry):

        valor = entry.get()
        numeros = "".join(c for c in valor if c.isdigit())[:8]

        dia = numeros[0:2]
        mes = numeros[2:4]
        anio = numeros[4:8]

        if len(dia) == 2:
            d = int(dia)
            if d < 1:
                dia = "01"
            elif d > 31:
                dia = "31"

        if len(mes) == 2:
            m = int(mes)
            if m < 1:
                mes = "01"
            elif m > 12:
                mes = "12"

        if len(anio) == 4:
            a = int(anio)
            if a < 1950:
                anio = "1950"

        formateado = dia
        if mes:
            formateado += "/" + mes
        if anio:
            formateado += "/" + anio

        entry.delete(0, "end")
        entry.insert(0, formateado)
        
    def _validar_fecha_inactividad(self, event=None):

        self._validar_fecha_generica(event.widget)
        self._actualizar_tiempo_inactividad()
        
    def _fecha_inactividad_valida(self, valor):

        if not re.match(r"^\d{2}/\d{2}/\d{4}$", valor):
            return False

        try:
            fecha = datetime.strptime(valor, "%d/%m/%Y")
        except ValueError:
            return False

        if fecha.year < 1950:
            return False

        return True
    
    def _normalizar_texto(self, texto):
        """Quita acentos y convierte a mayúsculas"""
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        return texto.upper().strip()

    def _actualizar_estado_especialidad(self, event=None):
        cargo = self._normalizar_texto(self.entry_cargo.get())
        requiere = cargo in self.cargos_requieren_especialidad

        if requiere:
            self.entry_especialidad.configure(state="normal")
            self.label_especialidad.configure(text="Especialidad *")
        else:
            self.entry_especialidad.configure(state="disabled")
            self.label_especialidad.configure(text="Especialidad")
            self._normal_entry(self.entry_especialidad)

    # =====================================================
    # BOTONES
    # =====================================================

    def _crear_botones(self):

        botones = tk.Frame(self, bg=COLOR_FONDO)
        botones.pack(fill="x", padx=15, pady=(0, 15))

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
        btn_cancelar.pack(side="left")
        
        texto_btn = "Actualizar médico" if self.medico_editar else "Guardar médico"

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
        btn_guardar.pack(side="right")

    # =====================================================
    # VALIDAR Y GUARDAR
    # =====================================================

    def guardar(self):
        
        self._normal_entry(self.entry_cedula)
        self._normal_entry(self.entry_nombres)
        self._normal_entry(self.entry_apellidos)
        self._normal_entry(self.entry_telefono)
        self._normal_entry(self.entry_correo)
        self._normal_entry(self.entry_fecha_ingreso)

        self._normal_entry(self.entry_cargo)
        self._normal_entry(self.entry_centro)
        self._normal_entry(self.entry_especialidad)

        cedula = self.entry_cedula.get().strip()
        nombres = self.entry_nombres.get().strip()
        codigo = self.entry_codigo.get().strip()
        apellidos = self.entry_apellidos.get().strip()
        telefono = self.entry_telefono.get().strip()
        correo = self.entry_correo.get().strip()
        cargo = self.entry_cargo.get().strip()
        especialidad = self.entry_especialidad.get().strip()
        centro = self.entry_centro.get().strip()
        
        hay_error = False

        # Validación de especialidad según cargo
        if self._normalizar_texto(cargo) in self.cargos_requieren_especialidad:
            if not especialidad:
                self._error_entry(self.entry_especialidad, "La especialidad es obligatoria para este cargo.")
                hay_error = True
        
        if not cedula or cedula == "V-":
            self._error_entry(self.entry_cedula, "La cédula es obligatoria.")
            hay_error = True
        elif not re.match(r"^V-\d{6,8}$", cedula):
            self._error_entry(self.entry_cedula, "Formato de cédula inválido (Ej: V-12345678).")
            hay_error = True
        else:
            # Verificación en base de datos
            medico_existente = buscar_por_cedula(cedula)
            if medico_existente:
                id_actual = self.medico_editar.get("id_medico") if self.medico_editar else None
                
                # Si se está creando o si en edición coincide con otro registro diferente
                if not self.medico_editar or medico_existente["id_medico"] != id_actual:
                    self._error_entry(self.entry_cedula, "La cédula ya se encuentra registrada.")
                    mostrar_error(
                        self,
                        "Cédula duplicada",
                        "Ya existe un médico registrado con esta cédula."
                    )
                    hay_error = True
            
        if not nombres:
            self._error_entry(self.entry_nombres, "El nombre es obligatorio.")
            hay_error = True
        elif not nombres.replace(" ", "").isalpha():
            self._error_entry(self.entry_nombres, "El nombre solo puede contener letras.")
            hay_error = True
        
        if not apellidos:
            self._error_entry(self.entry_apellidos, "El apellido es obligatorio.")
            hay_error = True
        elif not apellidos.replace(" ", "").isalpha():
            self._error_entry(self.entry_apellidos, "El apellido solo puede contener letras.")
            hay_error = True
        
        if codigo and not codigo.isdigit():
            self._error_entry(self.entry_codigo)
            hay_error = True

        
        if telefono:
            if not re.match(r"^0\d{10}$", telefono):
                # ✅ Agrega el texto del error como segundo parámetro
                self._error_entry(self.entry_telefono, "El teléfono debe tener 11 dígitos.")
                hay_error = True
        
        if correo:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", correo):
                self._error_entry(self.entry_correo, "Correo electrónico inválido.")
                hay_error = True
                
        fecha_ingreso = self.entry_fecha_ingreso.get().strip()
        if fecha_ingreso:
            if not self._fecha_valida(fecha_ingreso):
                self._error_entry(self.entry_fecha_ingreso)
                hay_error = True
        
        if not self.switch_estado.get():
            causa = self.entry_causa.get().strip()
            fecha_inicio = self.entry_fecha_inicio_inactividad.get().strip()
            fecha_fin = self.entry_fecha_fin_inactividad.get().strip()

            if not causa:
                self._error_entry(self.entry_causa, "La causa de inactividad es obligatoria.")
                hay_error = True

            if fecha_inicio:
                if not self._fecha_inactividad_valida(fecha_inicio):
                    self._error_entry(self.entry_fecha_inicio_inactividad, "Fecha inválida.")
                    hay_error = True

            if fecha_fin:
                if not self._fecha_inactividad_valida(fecha_fin):
                    self._error_entry(self.entry_fecha_fin_inactividad, "Fecha inválida.")
                    hay_error = True

            if (
                fecha_inicio
                and fecha_fin
                and self._fecha_inactividad_valida(fecha_inicio)
                and self._fecha_inactividad_valida(fecha_fin)
            ):
                inicio = datetime.strptime(fecha_inicio, "%d/%m/%Y")
                fin = datetime.strptime(fecha_fin, "%d/%m/%Y")

                if fin < inicio:
                    self._error_entry(self.entry_fecha_fin_inactividad, "La fecha fin no puede ser menor que la fecha inicio.")
                    hay_error = True

        if hay_error:
            return

        # ==========================================
        # FECHA INGRESO
        # ==========================================

        fecha_ingreso_db = None

        if fecha_ingreso:
            fecha_ingreso_db = datetime.strptime(
                fecha_ingreso,
                "%d/%m/%Y"
            ).date()

        # ==========================================
        # ESTATUS
        # ==========================================

        id_estatus = 1 if self.switch_estado.get() else 2

        fecha_inicio_inactividad_db = None
        fecha_fin_inactividad_db = None

        if not self.switch_estado.get():
            fecha_inicio = self.entry_fecha_inicio_inactividad.get().strip()
            fecha_fin = self.entry_fecha_fin_inactividad.get().strip()

            if fecha_inicio:
                fecha_inicio_inactividad_db = datetime.strptime(fecha_inicio, "%d/%m/%Y").date()
            if fecha_fin:
                fecha_fin_inactividad_db = datetime.strptime(fecha_fin, "%d/%m/%Y").date()

        # ==========================================
        # DATOS
        # ==========================================

        datos = {

            "cedula": cedula,
            "codigo": codigo,
            "nombres": nombres,
            "apellidos": apellidos,
            "telefono": telefono,
            "correo": correo,

            "id_dependencia": self.dependencia_actual,

            "id_tipo_contratacion":
                self.contratacion_actual,

            "ubicacion_administrativa":
                self.entry_ubicacion.get().strip(),

            "id_estatus": id_estatus,

            "formacion_estudiando":
                self.entry_formacion.get().strip(),

            "fecha_ingreso":
                fecha_ingreso_db,

            "cargo":
                self.entry_cargo.get().strip(),

            "especialidad":
                self.entry_especialidad.get().strip(),

            "centro_salud":
                self.entry_centro.get().strip(),

            "asic":
                self.entry_asic.get().strip(),

            "tipologia_centro":
                self.entry_tipologia.get().strip(),

            "causa_inactividad":
                (
                    self.entry_causa.get().strip()
                    if not self.switch_estado.get()
                    else None
                ),
                
            "fecha_inicio_inactividad":
                fecha_inicio_inactividad_db,

            "fecha_fin_inactividad":
                fecha_fin_inactividad_db,

            "tiempo_inactividad":
                self.entry_tiempo_inactividad.get().strip(),
        }

        if self.medico_editar:
            resultado = actualizar_medico(self.medico_editar["id_medico"], datos)
            titulo_mensaje = "Médico actualizado"
        else:
            resultado = crear_medico(datos)
            titulo_mensaje = "Médico registrado"

        if resultado["ok"]:
            mostrar_exito(
                self,
                titulo_mensaje,
                resultado["mensaje"]
            )
            self.destroy()
            if self.al_guardar:
                self.al_guardar()
        else:
            if "cédula" in resultado["mensaje"].lower():
                self._error_entry(self.entry_cedula, resultado["mensaje"])
                
            mostrar_error(
                self,
                "Error",
                resultado["mensaje"]
            )
    
    def _quitar_error(self, event):

        entry = event.widget
        entry.configure(border_color="#64748B")

        if hasattr(entry, "label_error"):
            entry.label_error.configure(text="")