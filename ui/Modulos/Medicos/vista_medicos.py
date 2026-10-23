import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from services.medico_service import (
    listar_medicos,
    obtener_medico,
    eliminar_medico as servicio_eliminar_medico
)
from ui.mensajes import mostrar_pregunta, mostrar_exito, mostrar_error
from services.exportar_medico_service import exportar_medico_pdf, exportar_medico_excel
import unicodedata
import re
from .ventana_exportar_medicos import VentanaExportarMedicos
from ui.sesion import es_admin,  rol_actual


from .colores import (
    COLOR_FONDO,
    COLOR_BLANCO,
    COLOR_TEXTO,
    COLOR_SECUNDARIO,
    COLOR_AZUL,
    COLOR_AZUL_HOVER,
    COLOR_BORDE
)
from .barra_filtros import BarraFiltros
from .tarjeta_medico import TarjetaMedico
from ui.iconos import obtener_icono
from .perfil_medico import VentanaPerfilMedico
from .formulario_medico import VentanaFormularioMedico
from .ventana_grupo_articulo8 import VentanaGrupoArticulo8




class VistaMedicos(tk.Frame):

    def __init__(self, parent, filtro_inicial="todos"):
        super().__init__(
            parent,
            bg=COLOR_FONDO
        )

        self.filtro_inicial = filtro_inicial

        self.icon_agregar_medico = obtener_icono(
            "agregar_medico",
            18
        )

        self.icon_exportar = obtener_icono(
            "exportar",
            18
        )

        self.icon_grupos = obtener_icono(
            "grupos",
            18
        )

        self.pack(
            fill="both",
            expand=True
        )

        self.medicos = self._cargar_medicos()
        self.medicos_mostrados = []
        self.columnas_actuales = 0
        self._redibujando_grid = False
        self.crear_interfaz()

    def _cargar_medicos(self):

        try:

            medicos = listar_medicos()

            return medicos

        except Exception as error:

            print(
                f"[VistaMedicos] Error cargando médicos: {error}"
            )

            return []
        
    

    # ========================================================
    # INTERFAZ
    # ========================================================

    def crear_interfaz(self):

        # ----------------------------------------------------
        # CONTENEDOR PRINCIPAL
        # ----------------------------------------------------

        self.canvas = tk.Canvas(
            self,
            bg=COLOR_FONDO,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )
        
        self.frame_scroll = tk.Frame(
            self.canvas,
            bg=COLOR_FONDO
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.frame_scroll,
            anchor="nw"
        )
        
        self.frame_scroll.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(
                self.canvas_window,
                width=e.width
            )
        )
        
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(
                int(-1 * (e.delta / 120)),
                "units"
            )
        )

        # ----------------------------------------------------
        # ENCABEZADO
        # ----------------------------------------------------
        
        contenido = tk.Frame(
            self.frame_scroll,
            bg=COLOR_FONDO
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=25
        )

        self._crear_encabezado(contenido)

        # ----------------------------------------------------
        # BARRA DE BÚSQUEDA + FILTROS (componente aparte)
        # ----------------------------------------------------

        centros = self._centros_disponibles()
        cargos = self._cargos_disponibles()
        dependencias = self._dependencias_disponibles()
        especialidades = self._especialidades_disponibles()

        self.barra_filtros = BarraFiltros(
            contenido,
            al_cambiar=self.aplicar_filtros,
            centros_disponibles=centros,
            cargos_disponibles=cargos,
            especialidades_disponibles=especialidades,
            dependencias_disponibles=dependencias
        )

        self.barra_filtros.pack(
            fill="x",
            pady=(0, 20)
        )

        # ----------------------------------------------------
        # CONTADOR
        # ----------------------------------------------------

        informacion = tk.Frame(
            contenido,
            bg=COLOR_FONDO
        )

        informacion.pack(
            fill="x",
            pady=(0, 12)
        )

        self.label_contador = tk.Label(
            informacion,
            text="",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO
        )

        self.label_contador.pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # GRID DE TARJETAS (con scroll)
        # ----------------------------------------------------
        # ----------------------------------------------------
        # GRID DE TARJETAS
        # ----------------------------------------------------

        self.contenedor_grid = tk.Frame(
            contenido,
            bg=COLOR_FONDO
        )

        self.contenedor_grid.pack(
            fill="both",
            expand=True
        )
        
        self.contenedor_grid.bind(
            "<Configure>",
            lambda e: self._ajustar_columnas()
        )
        

        self.aplicar_filtro_inicial()
        
        

    def _crear_encabezado(self, contenedor):

        encabezado = tk.Frame(
            contenedor,
            bg=COLOR_FONDO
        )

        encabezado.pack(
            fill="x",
            pady=(0, 20)
        )

        bloque_titulo = tk.Frame(
            encabezado,
            bg=COLOR_FONDO
        )

        bloque_titulo.pack(
            side="left"
        )

        titulo = tk.Label(
            bloque_titulo,
            text="Médicos",
            font=("Segoe UI", 24, "bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO
        )

        titulo.pack(
            anchor="w"
        )

        subtitulo = tk.Label(
            bloque_titulo,
            text="Consulta y administra la información del personal médico.",
            font=("Segoe UI", 10),
            fg=COLOR_SECUNDARIO,
            bg=COLOR_FONDO
        )

        subtitulo.pack(
            anchor="w",
            pady=(3, 0)
        )

        boton_agregar = ctk.CTkButton(
            encabezado,
            text="Agregar médico",
            image=self.icon_agregar_medico,
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_BLANCO,
            fg_color=COLOR_AZUL_HOVER,
            hover_color=COLOR_AZUL,
            corner_radius=10,
            cursor="hand2",
            height=40,
            width=150,
            command=self.agregar_medico
        )

        boton_agregar.pack(
            side="right",
            pady=5
        )
        
        # La exportación de médicos es una acción exclusiva del administrador.
        if es_admin() or rol_actual() == "secretaria":
            boton_exportar = ctk.CTkButton(
                encabezado,
                text=" Exportar médicos",
                image=self.icon_exportar,
                compound="left",
                font=("Segoe UI", 14, "bold"),
                text_color=COLOR_BLANCO,
                fg_color="#6C757D",
                hover_color="#3A3C3E",
                corner_radius=10,
                cursor="hand2",
                height=40,
                width=180,
                command=self.exportar_medicos
            )

            boton_exportar.pack(
                side="right",
                pady=5,
                padx=(0, 10)
            )

        boton_grupos = ctk.CTkButton(
            encabezado,
            text="Gestionar grupos",
            image=self.icon_grupos,
            compound="left",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_BLANCO,
            fg_color=COLOR_AZUL,
            hover_color=COLOR_AZUL_HOVER,
            corner_radius=10,
            cursor="hand2",
            height=40,
            width=170,
            command=self.gestionar_grupos
        )

        boton_grupos.pack(
            side="right",
            pady=5,
            padx=(0, 10)
        )

    

    # ========================================================
    # CENTROS DISPONIBLES
    # ========================================================

    def _centros_disponibles(self):

        centros = {
            str(medico.get("centro")).strip()
            for medico in self.medicos
            if medico.get("centro")
            and str(medico.get("centro")).strip()
        }

        return sorted(
            centros,
            key=lambda x: x.lower()
        )
    
    # ========================================================
    # CARGOS DISPONIBLES
    # ========================================================

    def _cargos_disponibles(self):

        cargos = {
            str(medico.get("cargo")).strip()
            for medico in self.medicos
            if medico.get("cargo")
            and str(medico.get("cargo")).strip()
        }

        return sorted(
            cargos,
            key=lambda x: x.lower()
        )
        
    # ========================================================
    # ESPECIALIDADES DISPONIBLES
    # ========================================================

    def _especialidades_disponibles(self):

        especialidades = {
            str(medico.get("especialidad")).strip()
            for medico in self.medicos
            if medico.get("especialidad")
            and str(medico.get("especialidad")).strip()
        }

        return sorted(
            especialidades,
            key=lambda x: x.lower()
        )

    # ========================================================
    # MOSTRAR MÉDICOS
    # ========================================================

    def mostrar_medicos(self, medicos):

        self.medicos_mostrados = medicos

        # Cantidad de columnas según el ancho disponible
        ancho = self.contenedor_grid.winfo_width()

        # Mientras Tkinter todavía no conoce el ancho real
        if ancho <= 1:
            self.after(100, lambda: self.mostrar_medicos(medicos))
            return

        ancho_tarjeta = 320
        espacio = 14

        columnas = max(
            1,
            min(
                4,
                ancho // (ancho_tarjeta + espacio)
            )
        )

        self.columnas_actuales = columnas

        self._redibujando_grid = True

        # Limpiar tarjetas anteriores
        for widget in self.contenedor_grid.winfo_children():
            widget.destroy()

        # Configurar columnas
        for columna in range(columnas):
            self.contenedor_grid.grid_columnconfigure(
                columna,
                weight=0
            )

        # Crear tarjetas
        for indice, medico in enumerate(medicos):

            fila = indice // columnas
            columna = indice % columnas

            tarjeta = TarjetaMedico(
                self.contenedor_grid,
                medico,
                al_ver_perfil=self.ver_medico,
                al_editar=self.editar_medico,
                al_eliminar=self.eliminar_medico
            )

            tarjeta.grid(
                row=fila,
                column=columna,
                sticky="nw",
                padx=7,
                pady=7
            )

        self.label_contador.config(
            text=f"{len(medicos)} médicos encontrados"
        )

        self._redibujando_grid = False
        
    def _ajustar_columnas(self):

        if self._redibujando_grid:
            return

        if not self.medicos_mostrados:
            return

        ancho = self.contenedor_grid.winfo_width()

        if ancho <= 1:
            return

        ancho_tarjeta = 350
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

            self.mostrar_medicos(
                self.medicos_mostrados
            )

    # ========================================================
    # FILTRADO (texto + combos), todo en un solo lugar
    # ========================================================

    def aplicar_filtros(self):

        texto = self.barra_filtros.obtener_texto_busqueda()

        filtros = self.barra_filtros.obtener_filtros()

        resultados = []

        texto_normalizado = self._normalizar_busqueda(
            texto
        )

        texto_cedula = self._normalizar_cedula(
            texto
        )

        for medico in self.medicos:

            # ====================================================
            # BUSCADOR
            # ====================================================

            if texto:

                nombres = self._normalizar_busqueda(
                    medico.get("nombres", "")
                )

                apellidos = self._normalizar_busqueda(
                    medico.get("apellidos", "")
                )

                nombre_completo = self._normalizar_busqueda(
                    medico.get("nombre", "")
                )

                cedula = self._normalizar_cedula(
                    medico.get("cedula", "")
                )

                coincide_nombre = (
                    texto_normalizado in nombres
                    or texto_normalizado in apellidos
                    or texto_normalizado in nombre_completo
                )

                coincide_cedula = (
                    bool(texto_cedula)
                    and texto_cedula in cedula
                )

                if not (
                    coincide_nombre
                    or coincide_cedula
                ):
                    continue

            # ====================================================
            # DEPENDENCIA
            # ====================================================

            if not self._coincide(
                filtros["dependencia"],
                medico.get("dependencia"),
                valores_todos=("Todas", "Todos", "")
            ):
                continue

            # ====================================================
            # CARGO
            # ====================================================

            if not self._coincide(
                filtros["cargo"],
                medico.get("cargo"),
                valores_todos=("Todas", "Todos", "")
            ):
                continue
            
            # ====================================================
            # ESPECIALIDAD
            # ====================================================

            if not self._coincide(
                filtros["especialidad"],
                medico.get("especialidad"),
                valores_todos=("Todas", "Todos", "")
            ):
                continue

            # ====================================================
            # CENTRO DE SALUD
            # ====================================================

            if not self._coincide(
                filtros["centro"],
                medico.get("centro"),
                valores_todos=("Todas", "Todos", "")
            ):
                continue

            # ====================================================
            # ESTATUS
            # ====================================================

            if not self._coincide(
                filtros["estatus"],
                medico.get("estatus"),
                valores_todos=("Todas", "Todos", "")
            ):
                continue

            resultados.append(medico)

        self.mostrar_medicos(
            resultados
        )

    @staticmethod
    def _coincide(
        valor_filtro,
        valor_medico,
        valores_todos
    ):

        if valor_filtro in valores_todos:
            return True

        if valor_medico is None:
            return False

        return (
            str(valor_filtro).strip().lower()
            ==
            str(valor_medico).strip().lower()
        )

    # ========================================================
    # VER MÉDICO
    # ========================================================

    def ver_medico(self, medico):
        # Obtener los datos completos del médico (incluyendo guardias) desde la BD
        datos_completos = obtener_medico(medico["id_medico"])
        
        if datos_completos:
            VentanaPerfilMedico(
                self,
                datos_completos
            )
        else:
            print("Error: No se pudo encontrar el médico en la base de datos.")

    # ========================================================
    # AGREGAR MÉDICO
    # ========================================================

    
    def exportar_medicos(self):

        # ==========================================================
        # OBTENER FILTROS ACTUALES
        # ==========================================================

        filtros = self.barra_filtros.obtener_filtros()

        texto_busqueda = (
            self.barra_filtros
            .obtener_texto_busqueda()
            .strip()
        )

        # Copia para poder mostrar la búsqueda como filtro
        filtros_exportacion = dict(filtros)

        if texto_busqueda:
            filtros_exportacion["Búsqueda"] = texto_busqueda

        # ==========================================================
        # ABRIR VENTANA DE EXPORTACIÓN
        # ==========================================================

        VentanaExportarMedicos(
            self,
            total_medicos=len(self.medicos),
            medicos_filtrados=self.medicos_mostrados,
            filtros_aplicados=filtros_exportacion,
            al_exportar=self._procesar_exportacion_medicos
        )
        
    
    def _procesar_exportacion_medicos(self, formato, alcance, medicos, filtros):
        # PDF
        if formato == "pdf":
            from services.exportar_medico_service import exportar_lista_medicos_pdf
            exportar_lista_medicos_pdf(medicos, filtros, self)

        # EXCEL
        elif formato == "excel":
            from services.exportar_medico_service import exportar_lista_medicos_excel
            exportar_lista_medicos_excel(medicos, filtros, self)





    # ========================================================
    # EDITAR / ELIMINAR (placeholders desde el menú "⋮")
    # ========================================================

    def editar_medico(self, medico):

        # Aquí luego se conectará con el formulario de edición
        # y con la base de datos.
        print(f"Editar: {medico['nombre']}")

    def eliminar_medico(self, medico):
        id_medico = medico.get("id_medico")
        nombre_medico = medico.get("nombre") or f"{medico.get('nombres', '')} {medico.get('apellidos', '')}".strip()

        if not id_medico:
            mostrar_error(self, "Error", "No se pudo identificar el código del médico.")
            return

        confirmado = mostrar_pregunta(
            parent=self,
            titulo="¿Eliminar médico?",
            mensaje=f"¿Está seguro de eliminar al Dr. {nombre_medico}?\n\nAl eliminar este médico se borrará permanentemente toda su información del sistema, incluyendo sus guardias registradas."
        )

        if confirmado:
            resultado = servicio_eliminar_medico(id_medico)

            if resultado.get("ok"):
                mostrar_exito(
                    parent=self,
                    titulo="Médico eliminado",
                    mensaje=resultado.get("mensaje")
                )
                self.recargar_medicos()
            else:
                mostrar_error(
                    parent=self,
                    titulo="Error al eliminar",
                    mensaje=resultado.get("mensaje")
                )

    # ========================================================
    # ANCHO DEL CANVAS
    # ========================================================

    def actualizar_ancho_contenedor(self, event):

        self.canvas.itemconfig(
            self.canvas_window,
            width=event.width
        )
        
   
    

    def agregar_medico(self):
        VentanaFormularioMedico(self, al_guardar=self.recargar_medicos)

    def gestionar_grupos(self):
        """Abre la administración de grupos Artículo 8: integrantes y
        el horario de guardias que comparten."""
        VentanaGrupoArticulo8(
            self,
            al_guardar=self.recargar_medicos
        )
        
    def recargar_medicos(self):
        """Recarga la lista de médicos desde la base de datos y actualiza la vista."""
        self.medicos = self._cargar_medicos()
        self.aplicar_filtros()
        
    
    
    @staticmethod
    def _normalizar_busqueda(valor):

        if valor is None:
            return ""

        valor = str(valor).strip().lower()

        # Eliminar acentos
        valor = unicodedata.normalize(
            "NFD",
            valor
        )

        valor = "".join(
            caracter
            for caracter in valor
            if unicodedata.category(caracter) != "Mn"
        )

        return valor
    
    @staticmethod
    def _normalizar_cedula(valor):
        if valor is None:
            return ""
        
        # Convierte a mayúsculas y elimina espacios
        valor = str(valor).strip().upper()
        
        # Mantiene solo números y las letras V o E (común en cédulas venezolanas)
        return re.sub(r'[^0-9VE]', '', valor)
    
    # ========================================================
    # DEPENDENCIAS DISPONIBLES
    # ========================================================

    def _dependencias_disponibles(self):

        dependencias = {
            str(medico.get("dependencia")).strip()
            for medico in self.medicos
            if medico.get("dependencia")
            and str(medico.get("dependencia")).strip()
        }

        return sorted(
            dependencias,
            key=lambda x: x.lower()
        )
        
    def aplicar_filtro_inicial(self):

        filtro = self.filtro_inicial

        # ----------------------------------------------------
        # TODOS
        # ----------------------------------------------------

        if filtro == "todos":

            resultados = self.medicos

            self.barra_filtros.establecer_filtro(
                "estatus",
                "Todos"
            )

        # ----------------------------------------------------
        # ACTIVOS
        # ----------------------------------------------------

        elif filtro == "activos":

            resultados = [
                medico
                for medico in self.medicos
                if str(
                    medico.get("estatus", "")
                ).strip().lower() == "activo"
            ]

            self.barra_filtros.establecer_filtro(
                "estatus",
                "Activo"
            )

        # ----------------------------------------------------
        # INACTIVOS
        # ----------------------------------------------------

        elif filtro == "inactivos":

            resultados = [
                medico
                for medico in self.medicos
                if str(
                    medico.get("estatus", "")
                ).strip().lower() == "inactivo"
            ]

            self.barra_filtros.establecer_filtro(
                "estatus",
                "Inactivo"
            )

        # ----------------------------------------------------
        # ESPECIALISTAS
        # ----------------------------------------------------

        elif filtro == "especialistas":

            resultados = [
                medico
                for medico in self.medicos
                if medico.get("especialidad")
                and str(
                    medico.get("especialidad")
                ).strip()
            ]

        # ----------------------------------------------------
        # ARTÍCULO 8
        # ----------------------------------------------------

        elif filtro == "art8":

            resultados = [
                medico
                for medico in self.medicos
                if self._normalizar_busqueda(
                    medico.get("cargo", "")
                ) == "articulo 8"
            ]

        # ----------------------------------------------------
        # POR DEFECTO
        # ----------------------------------------------------

        else:
            resultados = self.medicos

        self.mostrar_medicos(resultados)