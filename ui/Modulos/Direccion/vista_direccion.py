import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import customtkinter as ctk

from ui.iconos import obtener_icono
from services.personal_direccion_service import (
    listar_personal_direccion,
    obtener_personal_direccion,
    eliminar_personal_direccion,
    guardar_horario_direccion,
    obtener_calendario_horario_direccion,
    DIAS_SEMANA,
    DIAS_LABORALES_DIRECCION,
)
from services.exportar_personal_direccion_service import (
    exportar_horario_personal_pdf,
    mostrar_dialogo_exportar_asistencia,
)
from .formulario_personal import VentanaFormularioPersonalDireccion
from .perfil_personal_direccion import VentanaPerfilPersonalDireccion

COLOR_FONDO = "#F4F7FB"
COLOR_BLANCO = "#FFFFFF"
COLOR_TEXTO = "#0F172A"
COLOR_SECUNDARIO = "#64748B"
COLOR_AZUL = "#2563EB"
COLOR_AZUL_HOVER = "#0B4F94"
COLOR_BORDE = "#D5DEE8"
COLOR_VERDE = "#16A34A"
COLOR_ROJO = "#DC2626"

COLOR_DIA = "#FFFFFF"
COLOR_DIA_HOY = "#EFF6FF"
COLOR_HEADER_CALENDARIO = "#2563EB"

# Días que se pueden asignar en el horario del personal de dirección
DIAS = [(d, DIAS_SEMANA[d]) for d in DIAS_LABORALES_DIRECCION]


class VistaDireccion(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_FONDO)
        self.personas = []
        
        self.columnas_actuales = 0
        self._redibujando_lista = False

        hoy = date.today()
        self.mes_actual = hoy.month
        self.anio_actual = hoy.year
        self.horarios_mes = {}

        self.crear_interfaz()
        self.cargar_personal()

    def crear_interfaz(self):
        self.canvas = tk.Canvas(self, bg=COLOR_FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(self.canvas, bg=COLOR_FONDO)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._scroll)

        contenido = tk.Frame(self.scroll_frame, bg=COLOR_FONDO)
        contenido.pack(fill="both", expand=True, padx=35, pady=25)

        encabezado = tk.Frame(contenido, bg=COLOR_FONDO)
        encabezado.pack(fill="x", pady=(0, 18))

        bloque = tk.Frame(encabezado, bg=COLOR_FONDO)
        bloque.pack(side="left")
        tk.Label(bloque, text="Personal de Dirección", bg=COLOR_FONDO, fg=COLOR_TEXTO,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(bloque, text="Administra la información y los horarios del personal de dirección.",
                 bg=COLOR_FONDO, fg=COLOR_SECUNDARIO, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))

        self.icon_agregar = obtener_icono("agregar", 18)
        self.icon_exportar = obtener_icono("exportar", 18)

        ctk.CTkButton(
            encabezado, text="Agregar personal", image=self.icon_agregar,
            compound="left", width=165, height=40, corner_radius=8,
            fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
            font=("Segoe UI", 13, "bold"), command=self.agregar
        ).pack(side="right")

        ctk.CTkButton(
            encabezado,
            text="Exportar asistencia",
            image=self.icon_exportar,
            compound="left",
            width=180,
            height=40,
            corner_radius=8,
            fg_color="#6C757D",
            hover_color="#3A3C3E",
            font=("Segoe UI", 13, "bold"),
            command=self.exportar_asistencia
        ).pack(side="right", padx=(0, 10))

        barra = tk.Frame(contenido, bg=COLOR_BLANCO, highlightbackground=COLOR_BORDE, highlightthickness=1)
        barra.pack(fill="x", pady=(0, 14))
        self.icon_buscar = obtener_icono("buscar", 16)
        if self.icon_buscar:
            tk.Label(barra, image=self.icon_buscar, bg=COLOR_BLANCO).pack(side="left", padx=(12, 5), pady=8)
        self.busqueda = tk.Entry(barra, bg=COLOR_BLANCO, fg="#94A3B8", relief="flat",
                                 font=("Segoe UI", 12))
        self.busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=9)
        self.placeholder = "Buscar por nombre, cédula o cargo..."
        self.busqueda.insert(0, self.placeholder)
        self.busqueda.bind("<FocusIn>", self._limpiar_placeholder)
        self.busqueda.bind("<KeyRelease>", lambda e: self.aplicar_busqueda())

        self.contador = tk.Label(contenido, text="", bg=COLOR_FONDO, fg=COLOR_SECUNDARIO,
                                 font=("Segoe UI", 11))
        self.contador.pack(anchor="w", pady=(0, 12))

        self.lista = tk.Frame(contenido, bg=COLOR_FONDO)
        self.lista.pack(fill="both", expand=True)
        
        self.lista.bind(
            "<Configure>",
            lambda e: self._ajustar_columnas()
        )

        # ------------------------------------------------------
        # SECCIÓN: HORARIO DEL PERSONAL (CALENDARIO DEL MES)
        # ------------------------------------------------------

        separador_seccion = tk.Frame(contenido, bg="#E2E8F0", height=1)
        separador_seccion.pack(fill="x", pady=(30, 20))

        bloque_horario = tk.Frame(contenido, bg=COLOR_FONDO)
        bloque_horario.pack(fill="x", pady=(0, 14))
        tk.Label(bloque_horario, text="Horario del personal", bg=COLOR_FONDO, fg=COLOR_TEXTO,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(bloque_horario, text="Consulta qué integrantes del personal de dirección tienen horario asignado cada día.",
                 bg=COLOR_FONDO, fg=COLOR_SECUNDARIO, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))

        self.crear_navegacion_mes(contenido)

        self.contenedor_calendario = tk.Frame(
            contenido,
            bg=COLOR_FONDO
        )
        self.contenedor_calendario.pack(
            fill="both",
            expand=True,
            pady=(10, 5)
        )

        self.crear_calendario_horario()

        # ------------------------------------------------------
        # BOTÓN EXPORTAR HORARIO
        # ------------------------------------------------------

        self.icon_exportar_horario = obtener_icono("exportar", 18)

        ctk.CTkButton(
            contenido,
            text="Exportar horario",
            image=self.icon_exportar_horario,
            compound="left",
            width=180,
            height=40,
            corner_radius=8,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,
            font=("Segoe UI", 13, "bold"),
            command=self.exportar_horario
        ).pack(
            anchor="e",
            pady=(5, 20)
        )

    def _scroll(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _limpiar_placeholder(self, event):
        if self.busqueda.get() == self.placeholder:
            self.busqueda.delete(0, "end")
            self.busqueda.configure(fg=COLOR_TEXTO)

    def aplicar_busqueda(self):
        texto = self.busqueda.get().strip()
        if texto == self.placeholder:
            texto = ""
        self.pintar(listar_personal_direccion(texto))
        self.crear_calendario_horario()

    def cargar_personal(self):
        try:
            self.personas = listar_personal_direccion()
        except Exception as e:
            print(f"[VistaDireccion] Error: {e}")
            self.personas = []
        self.pintar(self.personas)
        self.crear_calendario_horario()

    def pintar(self, personas):

        for w in self.lista.winfo_children():
            w.destroy()

        self.contador.configure(
            text=f"{len(personas)} registro{'s' if len(personas) != 1 else ''}"
        )

        if not personas:
            self.columnas_actuales = 0

            tk.Label(
                self.lista,
                text="No hay personal registrado.",
                bg=COLOR_FONDO,
                fg=COLOR_SECUNDARIO,
                font=("Segoe UI", 12),
                pady=40
            ).pack(fill="x")

            return

        ancho = self.lista.winfo_width()

        if ancho <= 1:
            self.after(
                100,
                lambda: self.pintar(personas)
            )
            return

        ancho_tarjeta = 350
        espacio = 14

        columnas = max(
            1,
            min(
                4,
                ancho // (ancho_tarjeta + espacio)
            )
        )

        self.columnas_actuales = columnas

        self._redibujando_lista = True

        for columna in range(columnas):

            self.lista.grid_columnconfigure(
                columna,
                weight=0
            )

        for i, persona in enumerate(personas):

            fila = i // columnas
            columna = i % columnas

            self.crear_tarjeta(
                persona,
                fila,
                columna
            )

        self._redibujando_lista = False
        
    def _ajustar_columnas(self):

        if self._redibujando_lista:
            return

        if not self.personas:
            return

        ancho = self.lista.winfo_width()

        if ancho <= 1:
            return

        ancho_tarjeta = 300
        espacio = 14

        nuevas_columnas = max(
            1,
            min(
                4,
                ancho // (ancho_tarjeta + espacio)
            )
        )

        if nuevas_columnas != self.columnas_actuales:

            self.columnas_actuales = 0

            self.pintar(
                self.personas
            )

    def crear_tarjeta(self, persona, fila, columna):
        tarjeta = tk.Frame(
            self.lista, bg=COLOR_BLANCO, highlightbackground=COLOR_BORDE,
            highlightthickness=1, width=350, height=260
        )
        tarjeta.grid(row=fila, column=columna, sticky="nw", padx=7, pady=7)
        tarjeta.pack_propagate(False)

        color_estado = COLOR_VERDE if persona["activo"] else COLOR_ROJO
        estado = "ACTIVO" if persona["activo"] else "INACTIVO"

        # --- ENCABEZADO (NOMBRE, ICONO Y ESTATUS) ---
        top = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        top.pack(fill="x", padx=18, pady=(17, 6))

        # Contenedor del icono
        icono_fondo = tk.Frame(top, bg=COLOR_AZUL, width=38, height=38)
        icono_fondo.pack(side="left", anchor="n")
        icono_fondo.pack_propagate(False)

        icono_personal = obtener_icono("direccion", 20) 
        if icono_personal:
            icono_label = tk.Label(icono_fondo, image=icono_personal, bg=COLOR_AZUL)
            icono_label.image = icono_personal
            icono_label.place(relx=0.5, rely=0.5, anchor="center")

        # Contenedor derecho para el Nombre y el Estatus (alineado a la izquierda)
        info_top = tk.Frame(top, bg=COLOR_BLANCO)
        info_top.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Estatus alineado arriba a la derecha
        tk.Label(
            info_top, text=estado, bg=COLOR_BLANCO, fg=color_estado,
            font=("Segoe UI", 8, "bold")
        ).pack(side="right", anchor="ne")

        # Nombre alineado estrictamente a la izquierda
        tk.Label(
            info_top, text=persona["nombre"], bg=COLOR_BLANCO, fg=COLOR_TEXTO,
            font=("Segoe UI", 10, "bold"), wraplength=170, justify="left"
        ).pack(side="top", anchor="w")

        # --- CARGO (Alineado estrictamente a la izquierda debajo del nombre) ---
        cargo_frame = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        cargo_frame.pack(fill="x", padx=18, pady=(4, 0))

        tk.Label(
            cargo_frame, text=persona["cargo"] or "Personal de dirección", 
            bg=COLOR_BLANCO, fg=COLOR_TEXTO, font=("Segoe UI", 9), justify="left"
        ).pack(anchor="w")

        # --- DATOS DE CONTACTO E INFORMACIÓN ---
        fila_datos = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        fila_datos.pack(fill="x", pady=(10, 0))

        self._dato(fila_datos, "Cédula", persona["cedula"])
        self._dato(fila_datos, "Teléfono", persona["telefono"] or "No registrado")
        self._dato(fila_datos, "Correo", persona["correo"] or "No registrado")

        # Separador visual
        separador = tk.Frame(tarjeta, bg="#EEF2F7", height=1)
        separador.pack(fill="x", padx=18, pady=(12, 12))

        # --- PIE (BOTÓN VER PERFIL) ---
        pie = tk.Frame(tarjeta, bg=COLOR_BLANCO)
        pie.pack(fill="x", padx=18, pady=(0, 15))

        icono_ver = obtener_icono("ver", 16)
        boton_perfil = ctk.CTkButton(
            pie, text="Ver perfil", image=icono_ver, compound="left",
            font=("Segoe UI", 12, "bold"), text_color=COLOR_BLANCO,
            fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
            corner_radius=10, cursor="hand2", height=38,
            command=lambda p=persona: self.ver_perfil(p)
        )
        boton_perfil._icono = icono_ver 
        boton_perfil.pack(fill="x")

    def _dato(self, parent, etiqueta, valor):
        tk.Label(
            parent, text=f"{etiqueta}: {valor}", bg=COLOR_BLANCO, 
            fg=COLOR_SECUNDARIO, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=1)

    def agregar(self):
        VentanaFormularioPersonalDireccion(self, al_guardar=self.cargar_personal)

    def editar(self, persona):
        VentanaFormularioPersonalDireccion(self, persona=persona, al_guardar=self.cargar_personal)

    def eliminar(self, persona):
        if not messagebox.askyesno("Eliminar registro",
                                   f"¿Deseas eliminar a {persona['nombre']}?",
                                   parent=self):
            return
        resultado = eliminar_personal_direccion(persona["id_personal"])
        if resultado["ok"]:
            self.cargar_personal()
        else:
            messagebox.showerror("Error", resultado["mensaje"], parent=self)

    # ==========================================================
    # VER PERFIL
    # ==========================================================

    def ver_perfil(self, persona):
        persona_actual = obtener_personal_direccion(persona["id_personal"]) or persona
        VentanaPerfilPersonalDireccion(self, persona_actual)

    # ==========================================================
    # ASIGNAR HORARIO (SOLO DÍAS, SIN HORA)
    # ==========================================================

    def abrir_asignar_horario(self, persona):
        ventana = ctk.CTkToplevel(self)
        ventana.title(f"Horario - {persona['nombre']}")
        ventana.geometry("380x430")
        ventana.resizable(False, False)
        ventana.configure(fg_color=COLOR_BLANCO)
        ventana.transient(self)
        ventana.grab_set()

        ventana.after(10, lambda: self._centrar_ventana(ventana))

        ctk.CTkLabel(ventana, text="Asignar horario",
                     font=("Segoe UI", 21, "bold"), text_color=COLOR_TEXTO).pack(anchor="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(ventana, text=persona["nombre"],
                     font=("Segoe UI", 11), text_color=COLOR_SECUNDARIO).pack(anchor="w", padx=28, pady=(0, 18))

        dias_existentes = {h["dia"] for h in persona.get("horarios", [])}
        variables = {}
        cont = ctk.CTkFrame(ventana, fg_color="#F8FAFC", corner_radius=10)
        cont.pack(fill="both", expand=True, padx=28)

        for dia, nombre in DIAS:
            fila = ctk.CTkFrame(cont, fg_color="transparent")
            fila.pack(fill="x", padx=16, pady=8)
            var = tk.BooleanVar(value=dia in dias_existentes)
            ctk.CTkCheckBox(fila, text=nombre, variable=var,
                            text_color=COLOR_TEXTO, font=("Segoe UI", 12)).pack(side="left")
            variables[dia] = var

        def guardar():
            dias_seleccionados = [dia for dia, var in variables.items() if var.get()]
            resultado = guardar_horario_direccion(persona["id_personal"], dias_seleccionados)
            if resultado["ok"]:
                ventana.destroy()
                self.cargar_personal()
            else:
                messagebox.showerror("Error", resultado["mensaje"], parent=ventana)

        ctk.CTkButton(ventana, text="Guardar horario", width=180, height=40,
                      fg_color=COLOR_AZUL, hover_color=COLOR_AZUL_HOVER,
                      font=("Segoe UI", 12, "bold"), command=guardar).pack(pady=20)

    def _centrar_ventana(self, ventana):
        if not ventana.winfo_exists():
            return
        ventana.update_idletasks()
        ancho = ventana.winfo_width()
        alto = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana.winfo_screenheight() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ==========================================================
    # EXPORTAR (ASISTENCIA U HORARIO)
    # ==========================================================

    def exportar_asistencia(self):
        texto = self.busqueda.get().strip()

        if texto == self.placeholder:
            texto = ""

        mostrar_dialogo_exportar_asistencia(
            parent_window=self,
            texto_busqueda=texto
        )

    def exportar_horario(self):
        texto = self.busqueda.get().strip()

        if texto == self.placeholder:
            texto = ""

        exportar_horario_personal_pdf(
            anio=self.anio_actual,
            mes=self.mes_actual,
            texto_busqueda=texto,
            parent_window=self
        )

    # ==========================================================
    # CALENDARIO DE HORARIO DEL PERSONAL
    # ==========================================================

    def crear_navegacion_mes(self, parent):
        navegacion = tk.Frame(parent, bg=COLOR_FONDO)
        navegacion.pack(fill="x", pady=(0, 5))

        tk.Button(
            navegacion, text="‹", font=("Segoe UI", 24), fg=COLOR_TEXTO, bg=COLOR_BLANCO,
            activebackground="#E8F0FA", activeforeground=COLOR_AZUL, relief="flat", bd=0,
            width=3, cursor="hand2", command=self.mes_anterior
        ).pack(side="left")

        self.label_mes = tk.Label(
            navegacion, text="", font=("Segoe UI", 18, "bold"), fg=COLOR_TEXTO, bg=COLOR_FONDO
        )
        self.label_mes.pack(side="left", expand=True)

        tk.Button(
            navegacion, text="Hoy", font=("Segoe UI", 10, "bold"), fg=COLOR_AZUL, bg=COLOR_BLANCO,
            activebackground="#E8F0FA", activeforeground=COLOR_AZUL_HOVER, relief="solid", bd=1,
            highlightthickness=0, padx=12, pady=6, cursor="hand2", command=self.ir_a_hoy
        ).pack(side="right", padx=(0, 10))

        tk.Button(
            navegacion, text="›", font=("Segoe UI", 24), fg=COLOR_TEXTO, bg=COLOR_BLANCO,
            activebackground="#E8F0FA", activeforeground=COLOR_AZUL, relief="flat", bd=0,
            width=3, cursor="hand2", command=self.mes_siguiente
        ).pack(side="right")

    def crear_calendario_horario(self):
        for widget in self.contenedor_calendario.winfo_children():
            widget.destroy()

        nombre_mes = self.obtener_nombre_mes(self.mes_actual)
        self.label_mes.config(text=f"{nombre_mes} {self.anio_actual}")

        texto = self.busqueda.get().strip()
        if texto == self.placeholder:
            texto = ""

        try:
            self.horarios_mes = obtener_calendario_horario_direccion(
                self.anio_actual, self.mes_actual, texto_busqueda=texto
            )
        except Exception as e:
            print(f"[VistaDireccion] Error cargando horario del mes: {e}")
            self.horarios_mes = {}

        dias_semana = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

        for columna, dia in enumerate(dias_semana):
            encabezado = tk.Label(
                self.contenedor_calendario, text=dia, font=("Segoe UI", 10, "bold"),
                fg="white", bg=COLOR_HEADER_CALENDARIO, pady=9
            )
            encabezado.grid(row=0, column=columna, sticky="nsew", padx=1, pady=(0, 1))
            self.contenedor_calendario.grid_columnconfigure(columna, weight=1, uniform="calendario")

        cal = calendar.Calendar(firstweekday=6)
        semanas = cal.monthdayscalendar(self.anio_actual, self.mes_actual)

        for fila, semana in enumerate(semanas, start=1):
            self.contenedor_calendario.grid_rowconfigure(fila, weight=1, minsize=100)

            for columna, numero_dia in enumerate(semana):
                if numero_dia == 0:
                    celda = tk.Frame(
                        self.contenedor_calendario, bg="#E9EEF5",
                        highlightbackground=COLOR_BORDE, highlightthickness=1
                    )
                    celda.grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)
                    continue

                self.crear_celda_dia_horario(fila, columna, numero_dia)

    def crear_celda_dia_horario(self, fila, columna, numero_dia):
        hoy = date.today()
        fecha_dia = date(self.anio_actual, self.mes_actual, numero_dia)
        es_hoy = fecha_dia == hoy
        fondo = COLOR_DIA_HOY if es_hoy else COLOR_DIA

        celda = tk.Frame(
            self.contenedor_calendario, bg=fondo,
            highlightbackground=COLOR_BORDE, highlightthickness=1
        )
        celda.grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)

        tk.Label(
            celda, text=str(numero_dia), font=("Segoe UI", 11, "bold"),
            fg=COLOR_AZUL if es_hoy else COLOR_TEXTO, bg=fondo, anchor="w"
        ).pack(anchor="nw", padx=9, pady=7)

        zona_personal = tk.Frame(celda, bg=fondo)
        zona_personal.pack(fill="both", expand=True, padx=7, pady=(0, 7))

        asignados = self.horarios_mes.get(fecha_dia, [])

        if not asignados:
            tk.Label(
                zona_personal, text="Sin personal asignado", font=("Segoe UI", 8),
                fg=COLOR_SECUNDARIO, bg=fondo, anchor="w", justify="left"
            ).pack(anchor="nw", pady=(5, 0))
        else:
            for persona in asignados:
                tk.Label(
                    zona_personal, text=persona["nombre"], font=("Segoe UI", 8, "bold"),
                    fg=COLOR_TEXTO, bg=fondo, anchor="w", justify="left", wraplength=170
                ).pack(anchor="nw", fill="x", pady=(2, 3))

    def mes_anterior(self):
        self.mes_actual -= 1
        if self.mes_actual < 1:
            self.mes_actual = 12
            self.anio_actual -= 1
        self.crear_calendario_horario()

    def mes_siguiente(self):
        self.mes_actual += 1
        if self.mes_actual > 12:
            self.mes_actual = 1
            self.anio_actual += 1
        self.crear_calendario_horario()

    def ir_a_hoy(self):
        hoy = date.today()
        self.mes_actual = hoy.month
        self.anio_actual = hoy.year
        self.crear_calendario_horario()

    def obtener_nombre_mes(self, numero_mes):
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        return meses[numero_mes - 1]
