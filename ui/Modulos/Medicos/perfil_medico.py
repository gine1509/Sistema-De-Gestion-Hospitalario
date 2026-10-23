import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import date, datetime, timedelta
import calendar

import re

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
from services.medico_service import obtener_medico, eliminar_medico as servicio_eliminar_medico
from services.guardia_service import (
    obtener_guardias_medico,
    guardar_guardias_medico,
    obtener_grupo_medico,
)
from ui.mensajes import mostrar_pregunta, mostrar_exito, mostrar_error
from services.exportar_medico_service import exportar_medico_pdf, exportar_medico_excel
from ui.sesion import es_admin,  rol_actual
from .ventana_grupo_articulo8 import VentanaGrupoArticulo8



class VentanaPerfilMedico(ctk.CTkToplevel):

    def __init__(self, parent, medico):
        super().__init__(parent)

        self.medico = medico

        self.title("Perfil del Médico")
        self.geometry("650x700")
        self.resizable(False, False)

        self.configure(
            fg_color="#F4F7FB"
        )

        self.after(
            10,
            self._centrar
        )

        self.transient(parent)
        self.grab_set()

        self._cargar_iconos()
        self._crear_interfaz()
        

    # ==========================================================
    # CENTRAR
    # ==========================================================

    def _centrar(self):
        # Validar si la ventana sigue abierta/existiendo antes de operar
        if not self.winfo_exists():
            return

        self.update_idletasks()

        ancho = self.winfo_width()
        alto = self.winfo_height()

        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)

        self.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

    # ==========================================================
    # OBTENER VALOR
    # ==========================================================

    def _valor(self, clave, defecto="No registrado"):
        valor = self.medico.get(clave)

        if valor is None:
            return defecto

        if isinstance(valor, str):
            valor = valor.strip()

            if not valor:
                return defecto

        return str(valor)
    
        # ==========================================================
    # FORMACIÓN ACADÉMICA
    # ==========================================================

    def _formacion_academica(self):

        valor = self.medico.get("formacion_estudiando")

        if valor is None:
            return "No está cursando ninguna formación académica"

        if isinstance(valor, str):
            valor = valor.strip()

            if not valor:
                return "No está cursando ninguna formación académica"

        return str(valor)
    
    
    
    
    def _calcular_guardias(self):
        """Resumen de las guardias manuales del médico."""
        try:
            guardias = obtener_guardias_medico(self.medico["id_medico"])
            hoy = date.today()

            fechas = sorted(
                g["fecha_guardia"]
                for g in guardias
                if g.get("fecha_guardia")
            )

            anteriores = [f for f in fechas if f < hoy]
            futuras = [f for f in fechas if f >= hoy]

            ultima = (
                max(anteriores).strftime("%d/%m/%Y")
                if anteriores else "Aún no realizada"
            )

            if futuras:
                proxima_fecha = futuras[0]
                proxima = proxima_fecha.strftime("%d/%m/%Y")
                if proxima_fecha == hoy:
                    proxima += " (Hoy)"
            else:
                proxima = "—"

            return ultima, proxima, len(fechas)

        except Exception:
            return "—", "—", 0


    # ==========================================================
    # ICONOS
    # ==========================================================

    def _cargar_iconos(self):

        self.icono_personal = obtener_icono(
            "informacion_personal",
            20
        )

        self.icono_profesional = obtener_icono(
            "informacion_profesional",
            20
        )

        self.icono_guardias = obtener_icono(
            "horarios_y_guardias",
            20
        )
        
        self.guardias_blanco = obtener_icono(
                    "guardias_blanco",
                    20
        )

        self.icono_medico = obtener_icono(
            "medicos",
            28
        )

        self.icono_editar = obtener_icono(
            "editar",
            18
        )

        self.icono_exportar = obtener_icono(
            "descarga_azul",
            18
        )
        
        self.icono_guardar_pdf = obtener_icono(
            "guardar_pdf",
            42
        )

        self.icono_guardar_excel = obtener_icono(
            "guardar_excel",
            42
        )

        self.icono_eliminar = obtener_icono(
            "eliminar",
            18
        )

    # ==========================================================
    # INTERFAZ
    # ==========================================================

    def _crear_interfaz(self):

        prefijo = "Dr."

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

        header = tk.Frame(
            self,
            bg=COLOR_AZUL,
            height=100
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        fila_nombre = tk.Frame(
            header,
            bg=COLOR_AZUL
        )

        fila_nombre.pack(
            anchor="w",
            padx=25,
            pady=(12, 0)
        )

        if self.icono_medico:

            tk.Label(
                fila_nombre,
                image=self.icono_medico,
                bg=COLOR_AZUL
            ).pack(
                side="left",
                padx=(0, 8)
            )

        nombre = self.medico.get("nombre")
        if not nombre:
            nombres = self.medico.get("nombres", "") or ""
            apellidos = self.medico.get("apellidos", "") or ""
            nombre = f"{nombres} {apellidos}".strip()

        if not nombre:
            nombre = "Sin nombre"

        tk.Label(
            fila_nombre,
            text=f"{prefijo} {nombre}",
            font=("Segoe UI", 17, "bold"),
            fg="white",
            bg=COLOR_AZUL
        ).pack(
            side="left"
        )

        # Cargo

        cargo_header = tk.Label(
            header,
            text=self._valor(
                "cargo",
                "Cargo no registrado"
            ),
            font=("Segoe UI", 12, "bold"),
            fg="#DCE8FF",
            bg=COLOR_AZUL
        )

        cargo_header.pack(
            anchor="w",
            padx=25
        )

        # Cédula

        info_extra = tk.Label(
            header,
            text=f"C.I. {self._valor('cedula', 'No registrada')}",
            font=("Segoe UI", 12, "bold"),
            fg="#DCE8FF",
            bg=COLOR_AZUL
        )

        info_extra.pack(
            anchor="w",
            padx=25,
            pady=(2, 0)
        )

        # Estado (mantenemos la variable para la sección de Información Adicional)
        estatus = self._valor(
            "estatus",
            "No registrado"
        ).upper()

        # Botón Exportar reubicado en el encabezado
        if es_admin() or rol_actual() == "secretaria":
            btn_exportar = ctk.CTkButton(
                header,
                text="Exportar",
                image=self.icono_exportar,
                compound="left",
                font=("Segoe UI", 12, "bold"),
                text_color=COLOR_AZUL,
                fg_color=COLOR_BLANCO,
                hover_color="#E8F0FA",
                corner_radius=8,
                cursor="hand2",
                height=32,
                width=110,
                command=lambda: self.exportar_medico()
            )
            btn_exportar.place(
                relx=1,
                x=-25,
                y=30,
                anchor="ne"
            )

        # ------------------------------------------------------
        # CONTENIDO
        # ------------------------------------------------------

        contenedor = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        # ======================================================
        # INFORMACIÓN PERSONAL
        # ======================================================

        self._crear_seccion(
            contenedor,
            "Información personal",
            self.icono_personal,
            [

                (
                    "Cédula",
                    self._valor(
                        "cedula",
                        "No registrada"
                    )
                ),

                (
                    "Código",
                    self._valor(
                        "codigo"
                    )
                ),

                (
                    "Nombres",
                    self._valor(
                        "nombres"
                    )
                ),

                (
                    "Apellidos",
                    self._valor(
                        "apellidos"
                    )
                ),

                (
                    "Teléfono",
                    self._valor(
                        "telefono"
                    )
                ),

                (
                    "Correo",
                    self._valor(
                        "correo"
                    )
                )

            ]
        )

        

        # ======================================================
        # INFORMACIÓN PROFESIONAL
        # ======================================================

        self._crear_seccion(
            contenedor,
            "Información profesional",
            self.icono_profesional,
            [

                (
                    "Fecha de ingreso",
                    self._valor(
                        "fecha_ingreso"
                    )
                ),

                (
                    "Cargo",
                    self._valor(
                        "cargo"
                    )
                ),

                (
                    "Especialidad",
                    self._valor(
                        "especialidad"
                    )
                ),

                (
                    "Dependencia",
                    self._valor(
                        "dependencia"
                    )
                ),

                (
                    "Contratación",
                    self._valor(
                        "tipo_contratacion"
                    )
                ),

                (
                    "Formación académica",
                    self._formacion_academica()
                )

            ]
        )

        # ======================================================
        # UBICACIÓN LABORAL
        # ======================================================

        self._crear_seccion(
            contenedor,
            "Ubicación laboral",
            self.icono_guardias,
            [

                (
                    "Centro de salud",
                    self._valor(
                        "centro_salud"
                    )
                ),

                (
                    "ASIC",
                    self._valor(
                        "asic"
                    )
                ),

                (
                    "Ubicación administrativa",
                    self._valor(
                        "ubicacion_administrativa"
                    )
                ),

                (
                    "Tipología del centro",
                    self._valor("tipologia_centro")
                )

            ]
        )

       
        # ======================================================
        # GUARDIAS
        # ======================================================

        ultima_guardia, proxima_guardia, cantidad_guardias = self._calcular_guardias()

        self._crear_seccion(
            contenedor,
            "Información de guardias",
            self.icono_guardias,
            [
                ("Última guardia", ultima_guardia),
                ("Próxima guardia", proxima_guardia),
            ]
        )


        # ======================================================
        # ESTADO
        # ======================================================

        datos_estado = [

            (
                "Estatus",
                self._valor(
                    "estatus"
                )
            )

        ]

        # ------------------------------------------------------
        # INFORMACIÓN ADICIONAL SI ESTÁ INACTIVO
        # ------------------------------------------------------

        if estatus == "INACTIVO":

            datos_estado.extend([

                (
                    "Causa de inactividad",
                    self._valor(
                        "causa_inactividad"
                    )
                ),

                (
                    "Fecha inicio de inactividad",
                    self._valor(
                        "fecha_inicio_inactividad"
                    )
                ),

                (
                    "Fecha fin de inactividad",
                    self._valor(
                        "fecha_fin_inactividad"
                    )
                ),

                (
                    "Tiempo de inactividad",
                    self._valor(
                        "tiempo_inactividad"
                    )
                ),

                

            ])

        self._crear_seccion(
            contenedor,
            "Estado",
            self.icono_profesional,
            datos_estado
        )

        # ======================================================
        # BOTONES
        # ======================================================

        botones = tk.Frame(
            self,
            bg="#F4F7FB"
        )

        botones.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        # ------------------------------------------------------
        # ELIMINAR (solo administrador)
        # ------------------------------------------------------

        if es_admin():
            btn_eliminar = ctk.CTkButton(
                botones,
                text="Eliminar médico",
                image=self.icono_eliminar,
                compound="left",
                font=("Segoe UI", 13, "bold"),
                text_color="white",
                fg_color=COLOR_ROJO,
                hover_color="#B91C1C",
                corner_radius=10,
                cursor="hand2",
                height=42,
                width=170,
                command=lambda: self.eliminar_medico()
            )

            btn_eliminar.pack(
                side="left"
            )

        # ------------------------------------------------------
        # GUARDIAS
        # ------------------------------------------------------

        btn_guardias = ctk.CTkButton(
            botones,
            text="Guardias",
            image=self.guardias_blanco,
            compound="left",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=COLOR_VERDE,
            hover_color="#15803D",
            corner_radius=10,
            cursor="hand2",
            height=42,
            width=150,
            command=lambda: self.gestionar_guardias()
        )

        btn_guardias.pack(
            side="right",
            padx=(0, 10)
        )

        # ------------------------------------------------------
        # EDITAR
        # ------------------------------------------------------

        btn_editar = ctk.CTkButton(
            botones,
            text="Editar médico",
            image=self.icono_editar,
            compound="left",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=COLOR_AZUL_HOVER,
            hover_color=COLOR_AZUL,
            corner_radius=10,
            cursor="hand2",
            height=42,
            width=170,
            command=lambda: self.editar_medico()
        )

        btn_editar.pack(
            side="right",
            padx=(0,15),
        )

        

    # ==========================================================
    # ACCIONES
    # ==========================================================

    def editar_medico(self):
        from services.medico_service import obtener_medico
        from .formulario_medico import VentanaFormularioMedico 

        # Traemos todos los datos puros con los IDs usando el servicio
        medico_completo = obtener_medico(self.medico["id_medico"])

        if medico_completo:
            # self.master hace referencia a VistaMedicos, por lo que podemos usar su función de recargar
            VentanaFormularioMedico(
                self.master, 
                al_guardar=getattr(self.master, 'recargar_medicos', None),
                medico_editar=medico_completo
            )
            # Retrasamos la destrucción para evitar el conflicto de eventos en el canvas/focus
            self.after(50, self.destroy)

    def gestionar_guardias(self):
        """Abre el calendario manual de guardias del médico."""
        VentanaGestionGuardias(
            self,
            self.medico,
            al_guardar=self._actualizar_datos_guardias
        )

    def _actualizar_datos_guardias(self):
        datos = obtener_medico(self.medico["id_medico"])
        if datos:
            self.medico = datos
            # Reconstruimos el contenido completo para reflejar las
            # nuevas guardias sin alterar el diseño original.
            for widget in self.winfo_children():
                widget.destroy()
            self._cargar_iconos()
            self._crear_interfaz()

    def exportar_medico(self):
        # Obtener el nombre completo
        nombre = self.medico.get("nombre")

        if not nombre:
            nombres = self.medico.get("nombres", "") or ""
            apellidos = self.medico.get("apellidos", "") or ""
            nombre = f"{nombres} {apellidos}".strip() or "Sin nombre"

        # Actualizar la clave para las funciones de exportación
        self.medico["nombre"] = nombre

        # ==========================================================
        # VENTANA DE SELECCIÓN DE EXPORTACIÓN
        # ==========================================================
        dialogo = ctk.CTkToplevel(self)

        dialogo.title("Exportar Ficha")
        dialogo.geometry("420x260")
        dialogo.resizable(False, False)

        # Fondo blanco
        dialogo.configure(
            fg_color=COLOR_BLANCO
        )

        dialogo.transient(self)
        dialogo.grab_set()

        # ==========================================================
        # CENTRAR DIÁLOGO
        # ==========================================================
        dialogo.update_idletasks()

        ancho = 420
        alto = 260

        x = (
            self.winfo_x()
            + (self.winfo_width() // 2)
            - (ancho // 2)
        )

        y = (
            self.winfo_y()
            + (self.winfo_height() // 2)
            - (alto // 2)
        )

        dialogo.geometry(
            f"{ancho}x{alto}+{x}+{y}"
        )

        # ==========================================================
        # TÍTULO
        # ==========================================================
        ctk.CTkLabel(
            dialogo,
            text="Seleccione el formato de exportación",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_BLANCO
        ).pack(
            pady=(28, 22)
        )

        # ==========================================================
        # CONTENEDOR DE BOTONES
        # ==========================================================
        btn_frame = ctk.CTkFrame(
            dialogo,
            fg_color=COLOR_BLANCO
        )

        btn_frame.pack(
            fill="x",
            padx=35
        )

        btn_frame.grid_columnconfigure(
            0,
            weight=1
        )

        btn_frame.grid_columnconfigure(
            1,
            weight=1
        )

        def exportar_pdf_action():
            dialogo.withdraw()

            try:
                exportar_medico_pdf(
                    self.medico,
                    parent_window=self
                )
            finally:
                if dialogo.winfo_exists():
                    dialogo.destroy()


        def exportar_excel_action():
            dialogo.withdraw()

            try:
                exportar_medico_excel(
                    self.medico,
                    parent_window=self
                )
            finally:
                if dialogo.winfo_exists():
                    dialogo.destroy()

        # ==========================================================
        # BOTÓN PDF
        # ==========================================================
        btn_pdf = ctk.CTkButton(
            btn_frame,
            text="PDF",
            image=self.icono_guardar_pdf,
            compound="top",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=COLOR_ROJO,
            hover_color="#B91C1C",
            corner_radius=10,
            cursor="hand2",
            width=150,
            height=125,
            command=exportar_pdf_action
        )

        btn_pdf.grid(
            row=0,
            column=0,
            padx=(0, 10)
        )

        # ==========================================================
        # BOTÓN EXCEL
        # ==========================================================
        btn_excel = ctk.CTkButton(
            btn_frame,
            text="Excel",
            image=self.icono_guardar_excel,
            compound="top",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=COLOR_VERDE,
            hover_color="#15803D",
            corner_radius=10,
            cursor="hand2",
            width=150,
            height=125,
            command=exportar_excel_action
        )

        btn_excel.grid(
            row=0,
            column=1,
            padx=(10, 0)
        )

    def eliminar_medico(self):
        id_medico = self.medico.get("id_medico")
        nombre_medico = self.medico.get("nombre") or f"{self.medico.get('nombres', '')} {self.medico.get('apellidos', '')}".strip()

        if not id_medico:
            mostrar_error(self, "Error", "No se encontró el ID del médico.")
            return

        # Mostrar modal de advertencia previa a la eliminación
        confirmado = mostrar_pregunta(
            parent=self,
            titulo="¿Eliminar médico?",
            mensaje=f"¿Está seguro de eliminar al Dr. {nombre_medico}?\n\nAl eliminar este médico se borrará permanentemente toda su información del sistema, incluyendo sus guardias registradas."
        )

        if confirmado:
            resultado = servicio_eliminar_medico(id_medico)

            if resultado.get("ok"):
                mostrar_exito(
                    parent=self.master,
                    titulo="Médico eliminado",
                    mensaje=resultado.get("mensaje")
                )
                
                # Recargar el listado general si existe el callback
                if hasattr(self.master, 'recargar_medicos'):
                    self.master.recargar_medicos()

                self.destroy() # Cerrar la ventana del perfil
            else:
                mostrar_error(
                    parent=self,
                    titulo="Error al eliminar",
                    mensaje=resultado.get("mensaje")
                )

    # ==========================================================
    # SECCIONES
    # ==========================================================

    def _crear_seccion(
        self,
        parent,
        titulo,
        icono,
        datos
    ):

        tarjeta = tk.Frame(
            parent,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )

        tarjeta.pack(
            fill="x",
            pady=(0, 12)
        )

        encabezado = tk.Frame(
            tarjeta,
            bg=COLOR_BLANCO
        )

        encabezado.pack(
            fill="x",
            padx=15,
            pady=(15, 10)
        )

        if icono:

            tk.Label(
                encabezado,
                image=icono,
                bg=COLOR_BLANCO
            ).pack(
                side="left"
            )

        tk.Label(
            encabezado,
            text=titulo,
            font=("Segoe UI", 12, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(
            side="left",
            padx=(8, 0)
        )

        separador = tk.Frame(
            tarjeta,
            bg="#EEF2F7",
            height=1
        )

        separador.pack(
            fill="x",
            padx=15
        )

        contenido = tk.Frame(
            tarjeta,
            bg=COLOR_BLANCO
        )

        contenido.pack(
            fill="x",
            padx=15,
            pady=10
        )

        # 👇 1. CONFIGURACIÓN DE GRID: Forzar dos columnas de igual tamaño (50/50)
        contenido.grid_columnconfigure(0, weight=1, uniform="columna")
        contenido.grid_columnconfigure(1, weight=1, uniform="columna")

        fila_grid = 0  # Lleva el control de la fila actual en el grid

        for i in range(0, len(datos), 2):

            # --------------------------------------------------
            # COLUMNA IZQUIERDA
            # --------------------------------------------------

            izquierda = tk.Frame(
                contenido,
                bg=COLOR_BLANCO
            )

            # 👇 2. Usar grid en lugar de pack para ubicarlo estrictamente
            izquierda.grid(
                row=fila_grid, 
                column=0, 
                sticky="nw", 
                pady=6, 
                padx=(0, 10)
            )

            etiqueta1, valor1 = datos[i]

            tk.Label(
                izquierda,
                text=f"{etiqueta1}:",
                font=("Segoe UI", 10, "bold"),
                fg=COLOR_TEXTO,
                bg=COLOR_BLANCO
            ).pack(
                anchor="w"
            )

            tk.Label(
                izquierda,
                text=valor1 if valor1 else "No registrado",
                font=("Segoe UI", 10),
                fg=COLOR_SECUNDARIO,
                bg=COLOR_BLANCO,
                wraplength=250,
                justify="left"
            ).pack(
                anchor="w"
            )

            # --------------------------------------------------
            # COLUMNA DERECHA
            # --------------------------------------------------

            if i + 1 < len(datos):

                derecha = tk.Frame(
                    contenido,
                    bg=COLOR_BLANCO
                )

                # 👇 3. Usar grid para la segunda columna
                derecha.grid(
                    row=fila_grid, 
                    column=1, 
                    sticky="nw", 
                    pady=6, 
                    padx=(10, 0)
                )

                etiqueta2, valor2 = datos[i + 1]

                tk.Label(
                    derecha,
                    text=f"{etiqueta2}:",
                    font=("Segoe UI", 10, "bold"),
                    fg=COLOR_TEXTO,
                    bg=COLOR_BLANCO
                ).pack(
                    anchor="w"
                )

                tk.Label(
                    derecha,
                    text=valor2 if valor2 else "No registrado",
                    font=("Segoe UI", 10),
                    fg=COLOR_SECUNDARIO,
                    bg=COLOR_BLANCO,
                    wraplength=250,
                    justify="left"
                ).pack(
                    anchor="w"
                )
            
            # Avanzar a la siguiente fila del grid
            fila_grid += 1

# ==========================================================
# VENTANA DE GESTIÓN MANUAL DE GUARDIAS
# ==========================================================

class VentanaGestionGuardias(ctk.CTkToplevel):

    def __init__(self, parent, medico, al_guardar=None):
        super().__init__(parent)

        self.parent_perfil = parent
        self.medico = medico
        self.al_guardar = al_guardar

        self.title("Gestión de guardias")
        self.geometry("750x560")
        self.resizable(False, False)
        self.configure(fg_color="#F4F7FB")
        self.transient(parent)
        self.grab_set()

        hoy = date.today()
        self.mes_actual = hoy.month
        self.anio_actual = hoy.year

        self.fechas_seleccionadas = set()
        self.botones_dias = {}
        self.grupo_actual = None

        self._cargar_guardias()
        self._crear_interfaz()
        self._centrar()

    def _centrar(self):
        self.update_idletasks()
        ancho = 750
        alto = 560
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _cargar_guardias(self):
        try:
            guardias = obtener_guardias_medico(self.medico["id_medico"])
            self.fechas_seleccionadas = {
                g["fecha_guardia"]
                for g in guardias
                if g.get("fecha_guardia")
            }
        except Exception as e:
            self.fechas_seleccionadas = set()
            print(f"[GuardiasPerfil] Error cargando guardias: {e}")

        self._cargar_grupo()

    def _cargar_grupo(self):
        self.grupo_actual = obtener_grupo_medico(
            self.medico["id_medico"]
        )

    def _es_elegible_grupo(self):
        """Artículo 8 o Médico Interno pueden pertenecer a grupos."""
        cargo = (self.medico.get("cargo") or "").strip().upper()
        cargo_norm = (
            cargo
            .replace("Á", "A").replace("É", "E")
            .replace("Í", "I").replace("Ó", "O")
            .replace("Ú", "U")
        )
        return cargo_norm == "ARTICULO 8" or "INTERNO" in cargo_norm

    def _fecha_inactiva(self, fecha):
        inicio = self.medico.get("fecha_inicio_inactividad")
        fin = self.medico.get("fecha_fin_inactividad")

        def convertir(valor):
            if not valor:
                return None
            if isinstance(valor, datetime):
                return valor.date()
            if isinstance(valor, date):
                return valor
            texto = str(valor).strip()
            for formato in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(texto, formato).date()
                except ValueError:
                    pass
            return None

        inicio = convertir(inicio)
        fin = convertir(fin)

        if inicio and fin:
            return inicio <= fecha <= fin
        if inicio:
            return fecha >= inicio
        if fin:
            return fecha <= fin
        return False

    # ============================================================
    # INTERFAZ
    # ============================================================

    def _crear_interfaz(self):
        header = tk.Frame(self, bg=COLOR_AZUL, height=92)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Gestión de guardias",
            font=("Segoe UI", 19, "bold"),
            fg="white",
            bg=COLOR_AZUL
        ).pack(anchor="w", padx=25, pady=(14, 2))

        nombre = self.medico.get("nombre") or (
            f"{self.medico.get('nombres', '')} "
            f"{self.medico.get('apellidos', '')}"
        ).strip()

        tk.Label(
            header,
            text=f"Dr(a). {nombre}  •  {self.medico.get('cargo') or 'Sin cargo'}",
            font=("Segoe UI", 10, "bold"),
            fg="#DCE8FF",
            bg=COLOR_AZUL
        ).pack(anchor="w", padx=25)

        # ------------------------------------------------------
        # BOTONES FIJOS ABAJO
        # ------------------------------------------------------
        botones = tk.Frame(self, bg="#F4F7FB")
        botones.pack(side="bottom", fill="x", padx=20, pady=(0, 15))

        tk.Button(
            botones,
            text="Cancelar",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg="#E2E8F0",
            activebackground="#CBD5E1",
            relief="flat",
            bd=0,
            padx=20,
            pady=9,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right")

        self.btn_guardar = tk.Button(
            botones,
            text="Guardar guardias",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg=COLOR_AZUL,
            activebackground=COLOR_AZUL_HOVER,
            relief="flat",
            bd=0,
            padx=20,
            pady=9,
            cursor="hand2",
            command=self._guardar
        )
        self.btn_guardar.pack(side="right", padx=(0, 10))

        # Botón para ir a grupos (Artículo 8)
        self.btn_ver_grupos = tk.Button(
            botones,
            text="Ver grupos",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg=COLOR_AZUL,
            activebackground=COLOR_AZUL_HOVER,
            relief="flat",
            bd=0,
            padx=20,
            pady=9,
            cursor="hand2",
            command=self._abrir_grupos
        )
        # Se muestra solo cuando corresponde

        # ------------------------------------------------------
        # CONTENIDO
        # ------------------------------------------------------
        contenido = tk.Frame(self, bg="#F4F7FB")
        contenido.pack(fill="both", expand=True, padx=20, pady=15)

        es_elegible = self._es_elegible_grupo()
        tiene_grupo = bool(self.grupo_actual)

        # Modo solo lectura cuando pertenece a un grupo
        self.calendario_solo_lectura = es_elegible and tiene_grupo

        if es_elegible and tiene_grupo:
            self.btn_guardar.pack_forget()
            self.btn_ver_grupos.configure(text="Ver horario del grupo")
            self.btn_ver_grupos.pack(side="left")
            self._crear_aviso_con_grupo(contenido)
        elif es_elegible and not tiene_grupo:
            self.btn_ver_grupos.configure(text="Ver grupos")
            self.btn_ver_grupos.pack(side="left")
            self._crear_aviso_sin_grupo(contenido)
        else:
            self.btn_ver_grupos.pack_forget()

        # ------------------------------------------------------
        # NAVEGACIÓN + CALENDARIO (siempre visible)
        # ------------------------------------------------------
        nav = tk.Frame(contenido, bg="#F4F7FB")
        nav.pack(fill="x", pady=(0, 8))

        tk.Button(
            nav,
            text="‹",
            font=("Segoe UI", 22),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            activebackground="#E8F0FA",
            relief="flat",
            bd=0,
            width=3,
            cursor="hand2",
            command=self._mes_anterior
        ).pack(side="left")

        self.label_mes = tk.Label(
            nav,
            text="",
            font=("Segoe UI", 17, "bold"),
            fg=COLOR_TEXTO,
            bg="#F4F7FB"
        )
        self.label_mes.pack(side="left", expand=True)

        tk.Button(
            nav,
            text="›",
            font=("Segoe UI", 22),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO,
            activebackground="#E8F0FA",
            relief="flat",
            bd=0,
            width=3,
            cursor="hand2",
            command=self._mes_siguiente
        ).pack(side="right")

        calendario = tk.Frame(
            contenido,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        calendario.pack(fill="both", expand=True)

        self.calendario = calendario
        self._crear_calendario()

        # ------------------------------------------------------
        # LEYENDA
        # ------------------------------------------------------
        pie = tk.Frame(contenido, bg="#F4F7FB")
        pie.pack(fill="x", pady=(10, 0))

        tk.Label(
            pie,
            text="■ Guardia asignada",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_AZUL,
            bg="#F4F7FB"
        ).pack(side="left")

        tk.Label(
            pie,
            text="■ Día inactivo",
            font=("Segoe UI", 9, "bold"),
            fg="#94A3B8",
            bg="#F4F7FB"
        ).pack(side="left", padx=(18, 0))

        if self.calendario_solo_lectura:
            tk.Label(
                pie,
                text="■ Solo lectura (horario del grupo)",
                font=("Segoe UI", 9, "bold"),
                fg=COLOR_SECUNDARIO,
                bg="#F4F7FB"
            ).pack(side="left", padx=(18, 0))

        self.label_seleccion = tk.Label(
            pie,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_TEXTO,
            bg="#F4F7FB"
        )
        self.label_seleccion.pack(side="right")

    def _crear_aviso_con_grupo(self, contenedor):
        aviso = tk.Frame(
            contenedor,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        aviso.pack(fill="x", pady=(0, 12))

        tk.Label(
            aviso,
            text=f"Grupo: {self.grupo_actual['nombre']}",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(anchor="w", padx=15, pady=(10, 2))

        tk.Label(
            aviso,
            text=(
                f"Este médico pertenece al grupo «{self.grupo_actual['nombre']}». "
                "El calendario muestra el horario del grupo y no se puede editar aquí. "
                "Para modificar las fechas use «Ver horario del grupo»."
            ),
            font=("Segoe UI", 8),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            wraplength=680,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))

    def _crear_aviso_sin_grupo(self, contenedor):
        aviso = tk.Frame(
            contenedor,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1
        )
        aviso.pack(fill="x", pady=(0, 12))

        tk.Label(
            aviso,
            text="Grupo: Sin grupo",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_BLANCO
        ).pack(anchor="w", padx=15, pady=(10, 2))

        tk.Label(
            aviso,
            text=(
                "Este médico no pertenece a ningún grupo. "
                "Puede asignarle guardias de forma individual o incluirlo "
                "en un grupo con el botón «Ver grupos»."
            ),
            font=("Segoe UI", 8),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_BLANCO,
            wraplength=680,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))

    def _abrir_grupos(self):
        if self.grupo_actual:
            # Abrir el grupo concreto
            VentanaGrupoArticulo8(
                self,
                id_grupo_actual=self.grupo_actual["id_grupo"],
                al_guardar=self._refrescar_tras_grupo
            )
        else:
            # Abrir ventana de grupos (nuevo / listado)
            VentanaGrupoArticulo8(
                self,
                al_guardar=self._refrescar_tras_grupo
            )

    def _ver_horario_grupo(self):
        VentanaGrupoArticulo8(
            self,
            id_grupo_actual=self.grupo_actual["id_grupo"],
            al_guardar=self._refrescar_tras_grupo
        )

    def _refrescar_tras_grupo(self):
        self._cargar_guardias()
        for widget in self.winfo_children():
            widget.destroy()
        self._crear_interfaz()

    def _crear_calendario(self):
        for widget in self.calendario.winfo_children():
            widget.destroy()

        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
            "Diciembre"
        ]

        self.label_mes.configure(
            text=f"{meses[self.mes_actual - 1]} {self.anio_actual}"
        )

        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

        for columna, nombre in enumerate(dias_semana):
            self.calendario.grid_columnconfigure(columna, weight=1)
            tk.Label(
                self.calendario,
                text=nombre,
                font=("Segoe UI", 9, "bold"),
                fg=COLOR_BLANCO,
                bg=COLOR_AZUL,
                pady=6
            ).grid(
                row=0,
                column=columna,
                sticky="nsew",
                padx=1,
                pady=1
            )

        cal = calendar.Calendar(firstweekday=0)
        semanas = cal.monthdayscalendar(self.anio_actual, self.mes_actual)

        solo_lectura = getattr(self, "calendario_solo_lectura", False)

        for fila, semana in enumerate(semanas, start=1):
            self.calendario.grid_rowconfigure(fila, weight=1)

            for columna, numero in enumerate(semana):
                if numero == 0:
                    tk.Frame(
                        self.calendario,
                        bg="#F8FAFC"
                    ).grid(
                        row=fila,
                        column=columna,
                        sticky="nsew",
                        padx=1,
                        pady=1
                    )
                    continue

                fecha = date(
                    self.anio_actual,
                    self.mes_actual,
                    numero
                )

                inactivo = self._fecha_inactiva(fecha)
                seleccionado = fecha in self.fechas_seleccionadas
                hoy = fecha == date.today()

                if inactivo:
                    bg = "#E2E8F0"
                    fg = "#94A3B8"
                    active_bg = "#E2E8F0"
                    estado = "disabled"
                elif seleccionado:
                    bg = COLOR_AZUL
                    fg = "white"
                    active_bg = COLOR_AZUL_HOVER
                    # En solo lectura no se puede desmarcar
                    estado = "disabled" if solo_lectura else "normal"
                else:
                    bg = "#FFFFFF"
                    fg = COLOR_TEXTO
                    active_bg = "#EFF6FF"
                    estado = "disabled" if solo_lectura else "normal"

                boton = tk.Button(
                    self.calendario,
                    text=str(numero),
                    font=("Segoe UI", 9, "bold" if seleccionado or hoy else "normal"),
                    fg=fg,
                    bg=bg,
                    activeforeground=fg,
                    activebackground=active_bg,
                    disabledforeground=fg,
                    relief="solid" if hoy else "flat",
                    bd=1 if hoy else 0,
                    highlightthickness=0,
                    cursor="arrow" if estado == "disabled" else "hand2",
                    state=estado,
                    command=(
                        (lambda f=fecha: self._alternar_fecha(f))
                        if not solo_lectura else None
                    )
                )
                boton.grid(
                    row=fila,
                    column=columna,
                    sticky="nsew",
                    padx=2,
                    pady=2
                )
                self.botones_dias[fecha] = boton

        self._actualizar_contador()

    def _alternar_fecha(self, fecha):
        if getattr(self, "calendario_solo_lectura", False):
            return
        if self._fecha_inactiva(fecha):
            return

        if fecha in self.fechas_seleccionadas:
            self.fechas_seleccionadas.remove(fecha)
        else:
            self.fechas_seleccionadas.add(fecha)

        self._crear_calendario()

    def _actualizar_contador(self):
        self.label_seleccion.configure(
            text=f"{len(self.fechas_seleccionadas)} día(s) seleccionado(s)"
        )

    def _mes_anterior(self):
        self.mes_actual -= 1
        if self.mes_actual < 1:
            self.mes_actual = 12
            self.anio_actual -= 1
        self._crear_calendario()

    def _mes_siguiente(self):
        self.mes_actual += 1
        if self.mes_actual > 12:
            self.mes_actual = 1
            self.anio_actual += 1
        self._crear_calendario()

    def _guardar(self):
        # Este calendario solo se guarda para médicos sin grupo (o que
        # no son Artículo 8): el horario de un grupo se administra
        # exclusivamente desde VentanaGrupoArticulo8.
        resultado = guardar_guardias_medico(
            self.medico["id_medico"],
            sorted(self.fechas_seleccionadas),
            id_grupo_articulo8=None
        )

        if resultado.get("ok"):
            mostrar_exito(
                self,
                "Guardias guardadas",
                resultado.get("mensaje", "Guardias guardadas correctamente.")
            )
            if self.al_guardar:
                self.al_guardar()
            self.destroy()
        else:
            mostrar_error(
                self,
                "No se pudieron guardar",
                resultado.get("mensaje", "Ocurrió un error.")
            )
