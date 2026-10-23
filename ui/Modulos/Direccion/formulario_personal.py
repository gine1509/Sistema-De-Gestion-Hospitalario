import tkinter as tk
import customtkinter as ctk
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

# =====================================================
# COLORES
# =====================================================
# Se intenta usar el mismo módulo de colores que usa el resto de la
# aplicación (el mismo que usa formulario_medico.py). Si tu módulo de
# personal vive en otra carpeta, ajusta esta ruta de import.
try:
    from .colores import (
        COLOR_FONDO,
        COLOR_BLANCO,
        COLOR_TEXTO,
        COLOR_SECUNDARIO,
        COLOR_AZUL,
        COLOR_AZUL_HOVER,
        COLOR_BORDE,
        COLOR_ROJO,
    )
except ImportError:
    # Valores de respaldo (mismos tonos usados en el formulario de médicos)
    COLOR_FONDO = "#F4F7FB"
    COLOR_BLANCO = "#FFFFFF"
    COLOR_TEXTO = "#0F172A"
    COLOR_SECUNDARIO = "#64748B"
    COLOR_AZUL = "#2563EB"
    COLOR_AZUL_HOVER = "#0B4F94"
    COLOR_BORDE = "#D5DEE8"
    COLOR_ROJO = "#DC2626"

# =====================================================
# ICONOS (opcionales, no rompen si la clave no existe)
# =====================================================
try:
    from ui.iconos import obtener_icono
except ImportError:
    def obtener_icono(nombre, tamano=20):
        return None

# =====================================================
# SERVICIOS
# =====================================================
from services.personal_direccion_service import (
    crear_personal_direccion,
    actualizar_personal_direccion,
)

# buscar_por_cedula es opcional: si tu servicio aún no lo tiene, agrega
# una función similar a la de services/medico_service.py:
#
#   def buscar_por_cedula(cedula):
#       fila = db.fetch_one(
#           "SELECT * FROM personal_direccion WHERE cedula = %s", (cedula,)
#       )
#       return dict(fila) if fila else None
#
try:
    from services.personal_direccion_service import buscar_por_cedula
except ImportError:
    buscar_por_cedula = None

# =====================================================
# MENSAJES
# =====================================================
try:
    from ui.mensajes import mostrar_exito, mostrar_error
except ImportError:
    from tkinter import messagebox

    def mostrar_exito(parent, titulo, mensaje):
        messagebox.showinfo(titulo, mensaje, parent=parent)

    def mostrar_error(parent, titulo, mensaje):
        messagebox.showerror(titulo, mensaje, parent=parent)


class VentanaFormularioPersonalDireccion(ctk.CTkToplevel):

    def __init__(self, parent, persona=None, al_guardar=None):

        super().__init__(parent)
        self.parent = parent
        self.persona = persona
        self.al_guardar = al_guardar

        self.title("Editar personal de dirección" if persona else "Agregar personal de dirección")
        self.geometry("200x400")
        self.resizable(False, False)

        self.configure(fg_color=COLOR_FONDO)

        self.transient(parent)
        self.grab_set()

        self.icono_personal = obtener_icono("agregar_personal", 28)
        self.icono_guardar = obtener_icono("guardar", 18)
        self.icono_cancelar = obtener_icono("cancelar", 18)

        self._crear_interfaz()

        if self.persona:
            self._cargar_datos_persona()

        self.after(10, self._centrar)

    # =====================================================
    # CENTRAR
    # =====================================================

    def _centrar(self):
        self.update_idletasks()

        ancho = 620
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        # Limitar el alto máximo para que no se salga de la pantalla (dejando 100px de margen para la barra de tareas)
        alto = min(820, pantalla_alto - 100)

        x = (pantalla_ancho - ancho) // 2
        y = (pantalla_alto - alto) // 2

        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # =====================================================
    # INTERFAZ
    # =====================================================

    def _crear_interfaz(self):
        self._crear_header()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        self._crear_campos_personal(scroll)
        self._crear_estado(scroll)

        self._crear_botones()

    # =====================================================
    # HEADER
    # =====================================================

    def _crear_header(self):
        header = tk.Frame(self, bg=COLOR_AZUL, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        fila = tk.Frame(header, bg=COLOR_AZUL)
        fila.pack(anchor="w", padx=25, pady=(15, 0))

        if self.icono_personal:
            tk.Label(
                fila, image=self.icono_personal, bg=COLOR_AZUL
            ).pack(side="left", padx=(0, 8))

        titulo = "Editar personal de dirección" if self.persona else "Agregar personal de dirección"
        tk.Label(
            fila, text=titulo, font=("Segoe UI", 18, "bold"),
            fg="white", bg=COLOR_AZUL
        ).pack(side="left")

        tk.Label(
            header, text="Registro de personal de dirección",
            font=("Segoe UI", 11), fg="#DCE8FF", bg=COLOR_AZUL
        ).pack(anchor="w", padx=25)

    # =====================================================
    # TARJETA
    # =====================================================

    def _crear_tarjeta(self, parent, titulo):
        tarjeta = tk.Frame(
            parent, bg=COLOR_BLANCO,
            highlightbackground="#CBD5E1", highlightthickness=2,
            padx=10, pady=10
        )
        tarjeta.pack(fill="x", pady=(0, 12))

        tk.Label(
            tarjeta, text=titulo, font=("Segoe UI", 12, "bold"),
            fg=COLOR_TEXTO, bg=COLOR_BLANCO
        ).pack(anchor="w", padx=15, pady=(15, 10))

        contenido = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        contenido.pack(fill="x", padx=15, pady=(0, 15))

        return contenido

    # =====================================================
    # CAMPO
    # =====================================================

    def _campo(self, parent, texto):
        frame = tk.Frame(parent, bg=COLOR_BLANCO)
        tk.Label(
            frame, text=texto, font=("Segoe UI", 10, "bold"),
            bg=COLOR_BLANCO, fg=COLOR_TEXTO
        ).pack(anchor="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            frame, height=42, fg_color="#FFFFFF",
            border_color="#64748B", border_width=2,
            text_color="#0F172A", placeholder_text_color="#64748B",
            corner_radius=8
        )
        entry.pack(fill="x")

        label_error = tk.Label(
            frame, text="", font=("Segoe UI", 9),
            fg=COLOR_ROJO, bg=COLOR_BLANCO
        )
        label_error.pack(anchor="w", pady=(3, 0))
        entry.label_error = label_error

        entry.bind("<KeyRelease>", lambda e, ent=entry: self._normal_entry(ent), add="+")

        return frame, entry

    # =====================================================
    # ESTILOS VALIDACIÓN
    # =====================================================

    def _error_entry(self, entry, mensaje=""):
        entry.configure(border_color=COLOR_ROJO)
        if hasattr(entry, "label_error"):
            entry.label_error.configure(text=mensaje)

    def _normal_entry(self, entry):
        entry.configure(border_color="#64748B")
        if hasattr(entry, "label_error"):
            entry.label_error.configure(text="")

    # =====================================================
    # CAMPOS - INFORMACIÓN PERSONAL
    # =====================================================

    def _crear_campos_personal(self, parent):
        tarjeta = self._crear_tarjeta(parent, "Información del personal")

        tarjeta.grid_columnconfigure(0, weight=1)
        tarjeta.grid_columnconfigure(1, weight=1)

        campo, self.entry_cedula = self._campo(tarjeta, "Cédula *")
        campo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.entry_cedula.insert(0, "V-")
        self.entry_cedula.bind("<KeyRelease>", self._validar_cedula, add="+")

        campo, self.entry_telefono = self._campo(tarjeta, "Teléfono")
        campo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_telefono.configure(placeholder_text="04XXXXXXXXX")
        self.entry_telefono.bind("<KeyRelease>", self._validar_telefono, add="+")

        campo, self.entry_nombres = self._campo(tarjeta, "Nombres *")
        campo.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.entry_nombres.bind("<KeyRelease>", self._validar_nombre, add="+")

        campo, self.entry_apellidos = self._campo(tarjeta, "Apellidos *")
        campo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_apellidos.bind("<KeyRelease>", self._validar_apellido, add="+")

        campo, self.entry_correo = self._campo(tarjeta, "Correo electrónico")
        campo.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.entry_correo.bind("<KeyRelease>", self._validar_correo, add="+")

        campo, self.entry_cargo = self._campo(tarjeta, "Cargo")
        campo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.entry_cargo.bind("<KeyRelease>", self._validar_mayusculas, add="+")

        campo, self.entry_fecha_ingreso = self._campo(tarjeta, "Fecha de ingreso")
        campo.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        self.entry_fecha_ingreso.configure(placeholder_text="DD/MM/AAAA")
        self.entry_fecha_ingreso.bind("<KeyRelease>", self._validar_fecha_ingreso, add="+")

        campo, self.entry_observacion = self._campo(tarjeta, "Observación")
        campo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    # =====================================================
    # ESTADO (ACTIVO)
    # =====================================================

    def _crear_estado(self, parent):
        tarjeta = self._crear_tarjeta(parent, "Estado")

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

        self.switch_activo = ctk.CTkSwitch(
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
        self.switch_activo.select()
        self.switch_activo.pack(side="left")

        self.frame_inactivo = tk.Frame(tarjeta, bg=COLOR_BLANCO)

        campo, self.entry_causa = self._campo(
            self.frame_inactivo,
            "Causa de inactividad *"
        )
        campo.pack(fill="x")

        self.entry_causa.configure(
            placeholder_text="Ejemplo: Jubilado, Reposo, Permiso, Renuncia o Comisión de servicio"
        )

        tk.Label(
            self.frame_inactivo,
            text="Complete este campo únicamente cuando el personal se encuentre inactivo.",
            font=("Segoe UI", 9),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            wraplength=520,
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
        if self.switch_activo.get():
            self.label_estado.configure(text="Activo", fg="#16A34A")
            self.frame_inactivo.pack_forget()
        else:
            self.label_estado.configure(text="Inactivo", fg="#DC2626")
            self.frame_inactivo.pack(fill="x", pady=10)

    # =====================================================
    # BOTONES
    # =====================================================

    # =====================================================
    # BOTONES
    # =====================================================

    def _crear_botones(self):
        botones = tk.Frame(self, bg=COLOR_FONDO)
        botones.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            botones, text="Cancelar",
            image=self.icono_cancelar, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color="#6C757D", hover_color="#4B5563",
            corner_radius=10, cursor="hand2",
            height=44, width=160, command=self.destroy
        ).pack(side="left")

        texto_btn = "Actualizar personal" if self.persona else "Guardar personal"

        ctk.CTkButton(
            botones, text=texto_btn,
            image=self.icono_guardar, compound="left",
            font=("Segoe UI", 13, "bold"), text_color="white",
            fg_color=COLOR_AZUL_HOVER, hover_color=COLOR_AZUL,
            corner_radius=10, cursor="hand2",
            height=44, width=190, command=self.guardar
        ).pack(side="right")

    # =====================================================
    # VALIDACIONES EN VIVO
    # =====================================================

    def _validar_mayusculas(self, event):
        entry = event.widget
        valor = entry.get()
        cursor = entry.index("insert")

        entry.delete(0, "end")
        entry.insert(0, valor.upper())

        try:
            entry.icursor(cursor)
        except Exception:
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

    # =====================================================
    # INACTIVIDAD (fechas y cálculo de tiempo)
    # =====================================================

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

    # =====================================================
    # CARGAR DATOS (MODO EDICIÓN)
    # =====================================================

    def _cargar_datos_persona(self):
        p = self.persona

        self.entry_cedula.delete(0, "end")
        self.entry_cedula.insert(0, p.get("cedula", "V-"))

        self.entry_nombres.insert(0, str(p.get("nombres", "")).upper())
        self.entry_apellidos.insert(0, str(p.get("apellidos", "")).upper())
        self.entry_telefono.insert(0, str(p.get("telefono", "") or ""))
        self.entry_correo.insert(0, str(p.get("correo", "") or ""))
        self.entry_cargo.insert(0, str(p.get("cargo", "") or "").upper())
        self.entry_observacion.insert(0, str(p.get("observacion", "") or ""))

        fecha = p.get("fecha_ingreso")
        if fecha:
            texto_fecha = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else str(fecha)
            self.entry_fecha_ingreso.insert(0, texto_fecha)

        if p.get("activo", True):
            self.switch_activo.select()
            self._cambio_estado()
        else:
            self.switch_activo.deselect()
            self._cambio_estado()

            if p.get("causa_inactividad"):
                self.entry_causa.insert(0, p["causa_inactividad"])

            fecha_inicio_inact = p.get("fecha_inicio_inactividad")
            if fecha_inicio_inact:
                texto = (
                    fecha_inicio_inact.strftime("%d/%m/%Y")
                    if hasattr(fecha_inicio_inact, "strftime")
                    else str(fecha_inicio_inact)
                )
                self.entry_fecha_inicio_inactividad.insert(0, texto)

            fecha_fin_inact = p.get("fecha_fin_inactividad")
            if fecha_fin_inact:
                texto = (
                    fecha_fin_inact.strftime("%d/%m/%Y")
                    if hasattr(fecha_fin_inact, "strftime")
                    else str(fecha_fin_inact)
                )
                self.entry_fecha_fin_inactividad.insert(0, texto)

            if p.get("tiempo_inactividad"):
                self.entry_tiempo_inactividad.configure(state="normal")
                self.entry_tiempo_inactividad.insert(0, p["tiempo_inactividad"])
                self.entry_tiempo_inactividad.configure(state="disabled")

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

        cedula = self.entry_cedula.get().strip()
        nombres = self.entry_nombres.get().strip()
        apellidos = self.entry_apellidos.get().strip()
        telefono = self.entry_telefono.get().strip()
        correo = self.entry_correo.get().strip()
        cargo = self.entry_cargo.get().strip()
        observacion = self.entry_observacion.get().strip()
        fecha_ingreso = self.entry_fecha_ingreso.get().strip()

        hay_error = False

        # ---------- CÉDULA ----------
        if not cedula or cedula == "V-":
            self._error_entry(self.entry_cedula, "La cédula es obligatoria.")
            hay_error = True
        elif not re.match(r"^V-\d{6,8}$", cedula):
            self._error_entry(self.entry_cedula, "Formato de cédula inválido (Ej: V-12345678).")
            hay_error = True
        elif buscar_por_cedula is not None:
            persona_existente = buscar_por_cedula(cedula)
            if persona_existente:
                id_actual = self.persona.get("id_personal") if self.persona else None
                if not self.persona or persona_existente["id_personal"] != id_actual:
                    self._error_entry(self.entry_cedula, "La cédula ya se encuentra registrada.")
                    mostrar_error(
                        self, "Cédula duplicada",
                        "Ya existe personal registrado con esta cédula."
                    )
                    hay_error = True

        # ---------- NOMBRES ----------
        if not nombres:
            self._error_entry(self.entry_nombres, "El nombre es obligatorio.")
            hay_error = True
        elif not nombres.replace(" ", "").isalpha():
            self._error_entry(self.entry_nombres, "El nombre solo puede contener letras.")
            hay_error = True

        # ---------- APELLIDOS ----------
        if not apellidos:
            self._error_entry(self.entry_apellidos, "El apellido es obligatorio.")
            hay_error = True
        elif not apellidos.replace(" ", "").isalpha():
            self._error_entry(self.entry_apellidos, "El apellido solo puede contener letras.")
            hay_error = True

        # ---------- TELÉFONO ----------
        if telefono:
            if not re.match(r"^0\d{10}$", telefono):
                self._error_entry(self.entry_telefono, "El teléfono debe tener 11 dígitos (Ej: 04264283521).")
                hay_error = True

        # ---------- CORREO ----------
        if correo:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", correo):
                self._error_entry(self.entry_correo, "Correo electrónico inválido.")
                hay_error = True

        # ---------- FECHA DE INGRESO ----------
        if fecha_ingreso:
            if not self._fecha_valida(fecha_ingreso):
                self._error_entry(self.entry_fecha_ingreso, "Fecha inválida.")
                hay_error = True

        # ---------- INACTIVIDAD ----------
        causa = self.entry_causa.get().strip()
        fecha_inicio_inact = self.entry_fecha_inicio_inactividad.get().strip()
        fecha_fin_inact = self.entry_fecha_fin_inactividad.get().strip()

        if not self.switch_activo.get():

            if not causa:
                self._error_entry(self.entry_causa, "La causa de inactividad es obligatoria.")
                hay_error = True

            if fecha_inicio_inact:
                if not self._fecha_inactividad_valida(fecha_inicio_inact):
                    self._error_entry(self.entry_fecha_inicio_inactividad, "Fecha inválida.")
                    hay_error = True

            if fecha_fin_inact:
                if not self._fecha_inactividad_valida(fecha_fin_inact):
                    self._error_entry(self.entry_fecha_fin_inactividad, "Fecha inválida.")
                    hay_error = True

            if (
                fecha_inicio_inact
                and fecha_fin_inact
                and self._fecha_inactividad_valida(fecha_inicio_inact)
                and self._fecha_inactividad_valida(fecha_fin_inact)
            ):
                inicio = datetime.strptime(fecha_inicio_inact, "%d/%m/%Y")
                fin = datetime.strptime(fecha_fin_inact, "%d/%m/%Y")

                if fin < inicio:
                    self._error_entry(
                        self.entry_fecha_fin_inactividad,
                        "La fecha fin no puede ser menor que la fecha inicio."
                    )
                    hay_error = True

        if hay_error:
            return

        fecha_ingreso_db = None
        if fecha_ingreso:
            fecha_ingreso_db = datetime.strptime(fecha_ingreso, "%d/%m/%Y").date()

        # ---------- DATOS DE INACTIVIDAD (solo si está inactivo) ----------
        causa_inactividad_db = None
        fecha_inicio_inactividad_db = None
        fecha_fin_inactividad_db = None
        tiempo_inactividad_db = None

        if not self.switch_activo.get():
            causa_inactividad_db = causa

            if fecha_inicio_inact:
                fecha_inicio_inactividad_db = datetime.strptime(
                    fecha_inicio_inact, "%d/%m/%Y"
                ).date()

            if fecha_fin_inact:
                fecha_fin_inactividad_db = datetime.strptime(
                    fecha_fin_inact, "%d/%m/%Y"
                ).date()

            tiempo_inactividad_db = self.entry_tiempo_inactividad.get().strip()

        datos = {
            "cedula": cedula,
            "nombres": nombres,
            "apellidos": apellidos,
            "telefono": telefono,
            "correo": correo,
            "cargo": cargo,
            "observacion": observacion,
            "fecha_ingreso": fecha_ingreso_db,
            "activo": bool(self.switch_activo.get()),
            "causa_inactividad": causa_inactividad_db,
            "fecha_inicio_inactividad": fecha_inicio_inactividad_db,
            "fecha_fin_inactividad": fecha_fin_inactividad_db,
            "tiempo_inactividad": tiempo_inactividad_db,
        }

        if self.persona:
            resultado = actualizar_personal_direccion(self.persona["id_personal"], datos)
            titulo_mensaje = "Personal actualizado"
        else:
            resultado = crear_personal_direccion(datos)
            titulo_mensaje = "Personal registrado"

        if resultado["ok"]:
            mostrar_exito(self, titulo_mensaje, resultado.get("mensaje", "El personal ha sido agregado con éxito."))
            self.destroy()
            if self.al_guardar:
                self.al_guardar()
        else:
            if "cédula" in resultado["mensaje"].lower() or "cedula" in resultado["mensaje"].lower():
                self._error_entry(self.entry_cedula, resultado["mensaje"])

            mostrar_error(self, "Error", resultado["mensaje"])