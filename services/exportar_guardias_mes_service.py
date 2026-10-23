import os
import calendar
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog
import win32com.client
import shutil

from xhtml2pdf import pisa

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as ImagenExcel

from ui.mensajes import mostrar_exito, mostrar_error
from services.exportar_medico_service import link_callback, obtener_ruta_base
from services.exportar_guardias_service import obtener_mes_texto
from ui.Modulos.Medicos.colores import COLOR_BLANCO, COLOR_TEXTO, COLOR_ROJO, COLOR_VERDE


# ==============================================================================
# CONFIGURACIÓN DE FIRMAS DEL PIE DE PÁGINA
# ==============================================================================

FIRMA_JEFE_NOMBRE = "DR. RANULFO VIVAS"
FIRMA_JEFE_CARGO = "MÉDICO JEFE DEL SERV. DE GINECO-OBSTETRICIA HOSPITAL PBRO. JUSTO PASTOR ARIAS"

FIRMA_SUBDIRECTOR_NOMBRE = "DRA. MAGLYS DURAN"
FIRMA_SUBDIRECTOR_CARGO = "SUB DIRECTOR MÉDICO HOSPITAL PBRO. JUSTO PASTOR ARIAS"

FIRMA_DIRECTOR_NOMBRE = "CNEL. YONI ALBINO CARRILLO GARCÍA"
FIRMA_DIRECTOR_CARGO = "DIRECTOR DEL HOSPITAL PRESBÍTERO JUSTO PASTOR ARIAS DE RUBIO"
FIRMA_PROVIDENCIA = "PROVIDENCIA ADMINISTRATIVA N° 3792-2025 DE FECHA 05/05/2025"


# ==============================================================================
# UTILIDADES DE CALENDARIO / TEXTO
# ==============================================================================

_DIAS_SEMANA = ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"]

TAMANO_FUENTE_MEDICO = 11


def _prefijo_medico(especialidad):
    especialidad = (especialidad or "")
    if "Gineco" in especialidad or "Pediatra" in especialidad:
        return "DRA."
    return "DR."


def _construir_semanas(anio, mes, guardias_por_dia):
    cal = calendar.Calendar(firstweekday=6)  # 6 = Domingo
    semanas = []

    for semana in cal.monthdayscalendar(anio, mes):
        fila = []
        for numero_dia in semana:
            if numero_dia == 0:
                fila.append(None)
                continue

            fecha_dia = datetime(anio, mes, numero_dia).date()
            fila.append({
                "dia": numero_dia,
                "medicos": guardias_por_dia.get(fecha_dia, [])
            })
        semanas.append(fila)

    return semanas


def _texto_filtros(cargo, especialidad, centro, texto_busqueda):
    return [
        ("Cargo", cargo or "Todos los cargos"),
        ("Especialidad", especialidad or "Todas las especialidades"),
        ("Centro", centro or "Todos los centros"),
        ("Médico", texto_busqueda.strip() if texto_busqueda and texto_busqueda.strip() else "Todos"),
    ]


def _formatear_fecha_corta(fecha):
    return f"{fecha.day}-{fecha.month}"


def _recolectar_observaciones(medicos_inactivos_mes):
    observaciones = []

    for info in medicos_inactivos_mes:
        prefijo = _prefijo_medico(info.get("especialidad"))
        nombre_completo = f"{prefijo} {(info.get('nombre') or 'SIN NOMBRE').upper()}"
        causa = info.get("causa") or "Reposo médico"
        estado = "inactiva" if prefijo == "DRA." else "inactivo"

        fecha_inicio = info.get("fecha_inicio_inactividad")
        fecha_fin = info.get("fecha_fin_inactividad")

        # ------------------------------------------------------------
        # SALIDA DEFINITIVA (renuncia / jubilación)
        # ------------------------------------------------------------
        #
        # guardia_service.py ya se encarga de que este bloque solo
        # llegue aquí durante el mes exacto en que ocurrió la
        # renuncia/jubilación (fecha_inicio_inactividad). Por eso el
        # texto se redacta como un evento puntual de ese mes, y no
        # como un período de inactividad en curso.
        # ------------------------------------------------------------

        if info.get("es_definitiva"):

            causa_normalizada = causa.lower()
            verbo = (
                "se jubiló"
                if "jubil" in causa_normalizada
                else "renunció"
            )

            if fecha_inicio:
                observaciones.append(
                    f"{nombre_completo} {verbo} el "
                    f"{_formatear_fecha_corta(fecha_inicio)} "
                    f"del {fecha_inicio.year}."
                )
            else:
                observaciones.append(
                    f"{nombre_completo} {verbo}."
                )

            continue

        if fecha_inicio and fecha_fin:
            if fecha_inicio == fecha_fin:
                rango = f"el {_formatear_fecha_corta(fecha_inicio)} del {fecha_inicio.year}"
            elif fecha_inicio.year == fecha_fin.year:
                rango = (
                    f"del {_formatear_fecha_corta(fecha_inicio)} "
                    f"al {_formatear_fecha_corta(fecha_fin)} del {fecha_fin.year}"
                )
            else:
                rango = (
                    f"del {_formatear_fecha_corta(fecha_inicio)} del {fecha_inicio.year} "
                    f"al {_formatear_fecha_corta(fecha_fin)} del {fecha_fin.year}"
                )
        elif fecha_inicio:
            rango = f"desde el {_formatear_fecha_corta(fecha_inicio)} del {fecha_inicio.year}"
        elif fecha_fin:
            rango = f"hasta el {_formatear_fecha_corta(fecha_fin)} del {fecha_fin.year}"
        else:
            rango = "por tiempo indefinido"

        observaciones.append(f"{nombre_completo} está {estado} por {causa}, {rango}.")

    return observaciones


# ==============================================================================
# EXPORTAR GUARDIAS DEL MES A PDF
# ==============================================================================

def exportar_guardias_mes_pdf(
    anio,
    mes,
    guardias_por_dia,
    cargo="Todos los cargos",
    especialidad="Todas las especialidades",
    centro="Todos los centros",
    texto_busqueda="",
    parent_window=None
):
    mes_texto = obtener_mes_texto(mes)
    nombre_archivo = f"Reporte_Guardias_{mes_texto}_{anio}.pdf"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Reporte de Guardias del Mes (PDF)",
        initialfile=nombre_archivo,
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not filepath:
        return

    semanas = _construir_semanas(anio, mes, guardias_por_dia)
    filtros = _texto_filtros(cargo, especialidad, centro, texto_busqueda)
    medicos_inactivos_mes = guardias_por_dia.get("__medicos_inactivos_mes__", [])
    observaciones = _recolectar_observaciones(medicos_inactivos_mes)

    filtros_html = " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(
        f'<strong>{etiqueta}:</strong> {valor}'
        for etiqueta, valor in filtros
    )

    encabezado_dias = "".join(
        f'<th style="width: 14.28%;">{dia}</th>' for dia in _DIAS_SEMANA
    )

    filas_html = ""
    for semana in semanas:
        celdas_html = ""
        for celda in semana:
            if celda is None:
                celdas_html += '<td class="dia-vacio" style="width: 14.28%;"></td>'
                continue

            medicos_html = ""
            for medico in celda["medicos"]:
                prefijo = _prefijo_medico(medico.get("especialidad"))
                nombre = (medico.get("nombre") or "Sin nombre").upper()
                inactivo = medico.get("inactivo", False)

                reposo_html = '<div class="reposo-etiqueta">⚠ REPOSO MÉDICO</div>' if inactivo else ""

                medicos_html += (
                    f'<div class="medico-block">'
                    f'<div class="nombre-medico">{prefijo} {nombre}</div>'
                    f'{reposo_html}'
                    f'</div>'
                )

            celdas_html += (
                f'<td class="dia-celda" style="width: 14.28%;">'
                f'<div class="numero-dia">{celda["dia"]}</div>'
                f'{medicos_html}'
                f'</td>'
            )
        filas_html += f"<tr>{celdas_html}</tr>"

    observaciones_html = ""
    if observaciones:
        observaciones_html = (
            '<div class="section-title">OBSERVACIONES</div>'
            + ''.join(
                f'<div class="observacion-item">• {obs}</div>'
                for obs in observaciones
            )
        )
    else:
        observaciones_html = '<div class="section-title">OBSERVACIONES</div><div class="observacion-item">No se registran observaciones para este período.</div>'

    html_content = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: letter landscape;
                margin: 10mm 15mm 15mm 15mm;
            }}
            body {{ font-family: Arial, sans-serif; font-size: 8.5pt; }}
            .header-logos {{ width: 100%; text-align: center; border: none; margin-bottom: 15px; }}
            .header-logos td {{ text-align: center; vertical-align: middle; }}
            .header-logo-normal {{ height: 50px; }}
            .header-logo-salud {{ height: 130px; }}
            .header-logo-hospital {{ height: 85px; }}
            .header-logo-barrio {{ height: 35px; }}
            .title-container {{ text-align: center; margin-bottom: 15px; }}
            .report-title {{ font-size: 15pt; font-weight: bold; color: #000000; margin-top: 3px; margin-bottom: 3px; }}
            .date-title {{ font-size: 11pt; font-weight: bold; color: #0F4C81; }}
            .separator {{ border-top: 2px solid #0F4C81; margin-bottom: 15px; }}
            .filtros-box {{ text-align: center; font-size: 9pt; color: #444; margin-bottom: 15px; }}
            table.calendario {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 15px; }}
            table.calendario th {{ background-color: #2563EB; color: #FFFFFF; border: 1px solid #1E3A8A; padding: 4px 0; text-align: center; }}
            table.calendario td {{ border: 1px solid #94A3B8; vertical-align: top; padding: 4px 3px; }}
            .dia-vacio {{ background-color: #F1F5F9; }}
            .numero-dia {{ font-weight: bold; font-size: 10pt; color: #0F172A; }}
            .medico-block {{ text-align: center; margin-top: 3px; line-height: 1.1; }}
            .nombre-medico {{ font-weight: bold; font-size: 8pt; }}
            .reposo-etiqueta {{ font-size: 6.5pt; font-weight: bold; color: #B91C1C; margin-top: 1px; }}
            .section-title {{ font-size: 11pt; font-weight: bold; color: #0F4C81; margin: 15px 0 10px 0; }}
            .observacion-item {{
                font-size: 8.5pt;
                margin: 4px 0;
                padding-left: 10px;
                color: #333333;
            }}
            .firmas-tabla {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 25px;
                page-break-inside: avoid;
            }}

            .firmas-tabla td {{
                width: 50%;
                text-align: center;
                vertical-align: top;
                padding: 0 20px;
            }}

            .linea-firma {{
                border-top: 1px solid #000000;
                width: 80%;
                margin: 0 auto 6px auto;
            }}

            .firma-nombre {{
                font-family: Arial;
                font-size: 9pt;
                font-weight: bold;
                text-transform: uppercase;
            }}

            .firma-cargo {{
                font-family: Arial;
                font-size: 8pt;
                line-height: 1.2;
            }}

            .firma-providencia {{
                font-family: Arial;
                font-size: 7pt;
                line-height: 1.1;
            }}
        </style>
    </head>
    <body>
        <table class="header-logos">
            <tr>
                <td><img src="ui/Logos/Logo-Min-Salud-2009.png" class="header-logo-salud"></td>
                <td><img src="ui/Logos/logo.png" class="header-logo-hospital"></td>
                <td><img src="ui/Logos/Barrio-adentro.png" class="header-logo-barrio"></td>
                <td><img src="ui/Logos/spns.png" class="header-logo-normal"></td>
                <td><img src="ui/Logos/cropped-Logo-Nuevo-Fondo-Blanco-1.png" class="header-logo-normal"></td>
            </tr>
        </table>
        <div class="title-container">
            <div class="report-title">REPORTE DE GUARDIAS MÉDICAS</div>
            <div class="date-title">{mes_texto} {anio}</div>
        </div>
        <div class="separator"></div>
        <div class="filtros-box">{filtros_html}</div>
        <table class="calendario">
            <tr>{encabezado_dias}</tr>
            {filas_html}
        </table>
        {observaciones_html}
        <table class="firmas-tabla">
            <tr>
                <td align="center">
                    ______________________________________
                </td>

                <td align="center">
                    ______________________________________
                </td>
            </tr>

            <tr>
                <td align="center">
                    <b>{FIRMA_DIRECTOR_NOMBRE}</b>
                </td>

                <td align="center">
                    <b>{FIRMA_SUBDIRECTOR_NOMBRE}</b>
                </td>
            </tr>

            <tr>
                <td align="center">
                    {FIRMA_DIRECTOR_CARGO}
                </td>

                <td align="center">
                    {FIRMA_SUBDIRECTOR_CARGO}
                </td>
            </tr>

            <tr>
                <td align="center">
                    {FIRMA_PROVIDENCIA}
                </td>

                <td></td>
            </tr>
        </table>
    </body>
    </html>
    '''

    try:
        with open(filepath, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file, link_callback=link_callback)

        if pisa_status.err:
            mostrar_error(parent_window, "Error de exportación", "Hubo un problema al generar el PDF de las guardias del mes.")
        else:
            mostrar_exito(parent_window, "Exportación exitosa", "El reporte mensual de guardias se generó correctamente en PDF.")
            if os.name == 'nt':
                os.startfile(filepath)
    except Exception as e:
        mostrar_error(parent_window, "Error de exportación", f"No se pudo generar el PDF: {str(e)}")


# ==============================================================================
# EXPORTAR GUARDIAS DEL MES A EXCEL (USANDO PLANTILLA REAL Y WIN32COM)
# ==============================================================================

def exportar_guardias_mes_excel(
    anio,
    mes,
    guardias_por_dia,
    cargo="Todos los cargos",
    especialidad="Todas las especialidades",
    centro="Todos los centros",
    texto_busqueda="",
    parent_window=None
):
    mes_texto = obtener_mes_texto(mes)
    nombre_archivo = f"Reporte_Guardias_{mes_texto}_{anio}.xlsx"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Reporte de Guardias del Mes (Excel)",
        initialfile=nombre_archivo,
        defaultextension=".xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")]
    )

    if not filepath:
        return

    # ==========================================================================
    # LOCALIZAR PLANTILLA
    # ==========================================================================

    ruta_base = obtener_ruta_base()
    ruta_plantilla = os.path.join(
        ruta_base,
        "plantillas",
        "Plantilla_guardia_del_mes.xlsx"
    )

    if not os.path.isfile(ruta_plantilla):
        mostrar_error(
            parent_window,
            "Plantilla no encontrada",
            f"No se encontró la plantilla en:\n{ruta_plantilla}"
        )
        return

    # ==========================================================================
    # VERIFICAR EXCEL
    # ==========================================================================

    excel = None
    wb = None

    try:
        excel = win32com.client.Dispatch("Excel.Application")

    except Exception:
        mostrar_error(
            parent_window,
            "Excel no detectado",
            "Para exportar el reporte con formato completo es necesario "
            "tener instalado Microsoft Excel en este equipo."
        )
        return

    # ==========================================================================
    # DATOS
    # ==========================================================================

    semanas = _construir_semanas(
        anio,
        mes,
        guardias_por_dia
    )

    filtros = _texto_filtros(
        cargo,
        especialidad,
        centro,
        texto_busqueda
    )

    medicos_inactivos_mes = guardias_por_dia.get(
        "__medicos_inactivos_mes__",
        []
    )

    observaciones = _recolectar_observaciones(
        medicos_inactivos_mes
    )

    # ==========================================================================
    # CONSTANTES DE LA PLANTILLA
    # ==========================================================================

    # Fila donde está el título del mes.
    FILA_TITULO_MES = 5

    # Fila donde se muestran los filtros.
    FILA_FILTROS = 6

    # Primera fila del calendario.
    FILA_CALENDARIO_INICIO = 9

    # --------------------------------------------------------------------------
    # Estas dos filas corresponden a la plantilla original:
    #
    # 19 -> OBSERVACIONES
    # 20 -> primera fila de observación
    #
    # Si en tu plantilla cambias esas filas en el futuro, solo modificas
    # estas constantes.
    # --------------------------------------------------------------------------

    FILA_MODELO_TITULO_OBSERVACIONES = 19
    FILA_MODELO_OBSERVACION = 20

    # ==========================================================================
    # CONSTANTES DE EXCEL
    # ==========================================================================

    XL_MOVE_AND_SIZE = 1
    XL_PASTE_FORMATS = -4122
    XL_LEFT = -4131
    XL_CENTER = -4108

    try:

        # ======================================================================
        # COPIAR PLANTILLA
        # ======================================================================

        shutil.copy2(
            ruta_plantilla,
            filepath
        )

        excel.Visible = False
        excel.DisplayAlerts = False

        ruta_abs = os.path.abspath(filepath)

        wb = excel.Workbooks.Open(ruta_abs)

        # ======================================================================
        # OBTENER HOJA
        # ======================================================================

        try:
            ws = wb.Worksheets("Guardias del Mes")

        except Exception:

            try:
                ws = wb.Worksheets("Guardias")

            except Exception:
                ws = wb.Worksheets(1)

        # ======================================================================
        # CONFIGURAR OBJETOS DE LA PLANTILLA
        # ======================================================================

        try:
            for forma in ws.Shapes:
                forma.Placement = XL_MOVE_AND_SIZE
        except Exception:
            pass

        # ======================================================================
        # INYECTAR MES Y AÑO
        # ======================================================================

        try:
            ws.Cells(
                FILA_TITULO_MES,
                1
            ).Value = f"{mes_texto} {anio}"

        except Exception:
            pass

        # ======================================================================
        # INYECTAR FILTROS
        # ======================================================================

        texto_filtros_str = "   |   ".join(
            f"{etiqueta}: {valor}"
            for etiqueta, valor in filtros
        )

        try:
            ws.Cells(
                FILA_FILTROS,
                1
            ).Value = texto_filtros_str

        except Exception:
            pass

        # ======================================================================
        # INYECTAR CALENDARIO
        # ======================================================================

        fila_actual = FILA_CALENDARIO_INICIO

        for semana in semanas:

            # ------------------------------------------------------------------
            # FILA DE NÚMEROS DE LOS DÍAS
            # ------------------------------------------------------------------

            for col, celda_dia in enumerate(
                semana,
                start=1
            ):

                celda_num = ws.Cells(
                    fila_actual,
                    col
                )

                if celda_dia is None:
                    celda_num.Value = ""

                else:
                    celda_num.Value = celda_dia["dia"]

            fila_actual += 1

            # ------------------------------------------------------------------
            # FILA DE MÉDICOS
            # ------------------------------------------------------------------

            for col, celda_dia in enumerate(
                semana,
                start=1
            ):

                celda_m = ws.Cells(
                    fila_actual,
                    col
                )

                if (
                    celda_dia is None
                    or not celda_dia["medicos"]
                ):
                    celda_m.Value = ""

                else:

                    lineas = []

                    for medico in celda_dia["medicos"]:

                        prefijo = _prefijo_medico(
                            medico.get("especialidad")
                        )

                        nombre = (
                            medico.get("nombre")
                            or "Sin nombre"
                        ).upper()

                        lineas.append(
                            f"{prefijo} {nombre}"
                        )

                        if medico.get("inactivo"):
                            lineas.append(
                                "⚠ REPOSO MÉDICO"
                            )

                        lineas.append("")

                    celda_m.Value = "\n".join(
                        lineas
                    ).strip()

                    # Asegurar que el texto se ajuste dentro de la celda.
                    celda_m.WrapText = True

            fila_actual += 1

        # ==========================================================================
        # OBSERVACIONES DINÁMICAS
        # ==========================================================================
        #
        # Aquí está la corrección principal.
        #
        # La plantilla tiene:
        #
        #   FILA 19 -> encabezado OBSERVACIONES
        #   FILA 20 -> primera observación
        #
        # Cuando existen más observaciones:
        #
        #   19 -> OBSERVACIONES
        #   20 -> observación 1
        #   21 -> observación 2
        #   22 -> observación 3
        #
        # Las filas adicionales se INSERTAN, por lo que todo lo que esté
        # debajo (firmas, etc.) baja automáticamente.
        # ==========================================================================

        try:

            # ------------------------------------------------------------------
            # FILA DONDE COMIENZA OBSERVACIONES
            # ------------------------------------------------------------------

            fila_titulo_observaciones = fila_actual

            # ------------------------------------------------------------------
            # COPIAR FORMATO DEL ENCABEZADO DE OBSERVACIONES
            # ------------------------------------------------------------------

            ws.Rows(
                FILA_MODELO_TITULO_OBSERVACIONES
            ).Copy()

            ws.Rows(
                fila_titulo_observaciones
            ).PasteSpecial(XL_PASTE_FORMATS)

            excel.CutCopyMode = False

            # Escribir título
            ws.Cells(
                fila_titulo_observaciones,
                1
            ).Value = "OBSERVACIONES"

            # ------------------------------------------------------------------
            # DETERMINAR OBSERVACIONES
            # ------------------------------------------------------------------

            lista_observaciones = list(observaciones)

            if not lista_observaciones:
                lista_observaciones = [
                    "No se registran observaciones para este período."
                ]

            # ------------------------------------------------------------------
            # PRIMERA FILA DE OBSERVACIÓN
            # ------------------------------------------------------------------

            fila_obs = fila_titulo_observaciones + 1

            # ==================================================================
            # CREAR UNA FILA POR CADA OBSERVACIÓN
            # ==================================================================

            for indice, obs in enumerate(lista_observaciones):

                # ----------------------------------------------------------------
                # Para la segunda observación en adelante:
                #
                # INSERTAMOS UNA FILA COMPLETA.
                #
                # Esto hace que las firmas y cualquier contenido inferior
                # se desplace automáticamente hacia abajo.
                # ----------------------------------------------------------------

                if indice > 0:

                    ws.Rows(
                        fila_obs
                    ).Insert()

                # ----------------------------------------------------------------
                # COPIAR EL FORMATO DE LA FILA 20 DE LA PLANTILLA
                #
                # La fila 20 es nuestra fila modelo porque ya contiene:
                #
                # - bordes
                # - fondo gris
                # - alineación
                # - altura
                # - estructura visual
                # ----------------------------------------------------------------

                ws.Rows(
                    FILA_MODELO_OBSERVACION
                ).Copy()

                ws.Rows(
                    fila_obs
                ).PasteSpecial(XL_PASTE_FORMATS)

                excel.CutCopyMode = False

                # ----------------------------------------------------------------
                # COPIAR ALTURA DE LA FILA MODELO
                # ----------------------------------------------------------------

                try:
                    ws.Rows(
                        fila_obs
                    ).RowHeight = ws.Rows(
                        FILA_MODELO_OBSERVACION
                    ).RowHeight
                except Exception:
                    pass

                # ----------------------------------------------------------------
                # ESCRIBIR OBSERVACIÓN
                # ----------------------------------------------------------------

                celda_obs = ws.Cells(
                    fila_obs,
                    1
                )

                celda_obs.Value = f"• {obs}"

                # ----------------------------------------------------------------
                # FORMATO DEL TEXTO
                # ----------------------------------------------------------------

                try:
                    celda_obs.Font.Name = "Calibri"
                    celda_obs.Font.Size = 11
                    celda_obs.Font.Bold = False
                except Exception:
                    pass

                # ----------------------------------------------------------------
                # ALINEACIÓN
                # ----------------------------------------------------------------

                try:
                    celda_obs.HorizontalAlignment = XL_LEFT
                    celda_obs.VerticalAlignment = XL_CENTER
                except Exception:
                    pass

                # ----------------------------------------------------------------
                # AJUSTE DE TEXTO
                #
                # Lo dejamos desactivado para que la observación conserve
                # una sola línea como en la plantilla.
                # ----------------------------------------------------------------

                try:
                    celda_obs.WrapText = False
                except Exception:
                    pass

                # ----------------------------------------------------------------
                # LIMPIAR RESTO DE COLUMNAS
                #
                # La observación se escribe solamente en A.
                # B:G permanecen vacías, pero conservan los bordes/formato.
                # ----------------------------------------------------------------

                for col in range(2, 8):

                    try:
                        ws.Cells(
                            fila_obs,
                            col
                        ).Value = ""

                    except Exception:
                        pass

                # Siguiente fila
                fila_obs += 1

            # ==================================================================
            # LIMPIAR POSIBLES FILAS RESIDUALES
            # ==================================================================
            #
            # No borramos filas ni modificamos el formato.
            # Solo eliminamos texto de algunas filas posteriores que pudieran
            # contener información de ejemplo de la plantilla.
            #
            # Como las filas de firmas ya fueron desplazadas mediante Insert(),
            # no se pisan.
            # ==================================================================

            fila_despues_observaciones = fila_obs

            for i in range(2):

                try:
                    ws.Cells(
                        fila_despues_observaciones + i,
                        1
                    ).Value = ""

                except Exception:
                    pass

            # ------------------------------------------------------------------
            # LIMPIAR PORTAPAPELES
            # ------------------------------------------------------------------

            excel.CutCopyMode = False

        except Exception as e:
            print(
                f"Error al generar observaciones: {e}"
            )

        # ==========================================================================
        # GUARDAR
        # ==========================================================================

        wb.Save()

        wb.Close(
            SaveChanges=True
        )

        wb = None

        # ==========================================================================
        # MENSAJE DE ÉXITO
        # ==========================================================================

        mostrar_exito(
            parent_window,
            "Exportación exitosa",
            "El reporte mensual de guardias se generó correctamente en Excel."
        )

        # ==========================================================================
        # ABRIR ARCHIVO
        # ==========================================================================

        if os.name == "nt":
            os.startfile(filepath)

    except Exception as e:

        # ----------------------------------------------------------------------
        # CERRAR LIBRO SI OCURRIÓ UN ERROR
        # ----------------------------------------------------------------------

        try:
            if wb is not None:
                wb.Close(
                    SaveChanges=False
                )
        except Exception:
            pass

        mostrar_error(
            parent_window,
            "Error de exportación",
            f"No se pudo generar el Excel:\n{str(e)}"
        )

    finally:

        # ==========================================================================
        # CERRAR EXCEL
        # ==========================================================================

        try:
            if excel is not None:
                excel.DisplayAlerts = True
                excel.Quit()

        except Exception:
            pass


# ==============================================================================
# VENTANA DE DIÁLOGO: EXPORTAR GUARDIAS DEL MES
# ==============================================================================

def mostrar_dialogo_exportar_guardias_mes(
    anio,
    mes,
    guardias_por_dia,
    cargo="Todos los cargos",
    especialidad="Todas las especialidades",
    centro="Todos los centros",
    texto_busqueda="",
    parent_window=None
):
    dialogo = None

    try:
        dialogo = ctk.CTkToplevel(parent_window)
        dialogo.title("Exportar Guardias del Mes")
        dialogo.geometry("440x280")
        dialogo.resizable(False, False)
        dialogo.configure(fg_color=COLOR_BLANCO)

        if parent_window:
            dialogo.transient(parent_window)

        dialogo.grab_set()
        dialogo.update_idletasks()

        if parent_window and parent_window.winfo_exists():
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (440 // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (280 // 2)
        else:
            x = (dialogo.winfo_screenwidth() // 2) - (440 // 2)
            y = (dialogo.winfo_screenheight() // 2) - (280 // 2)

        dialogo.geometry(f"440x280+{x}+{y}")

        mes_texto = obtener_mes_texto(mes).title()

        ctk.CTkLabel(
            dialogo,
            text="Exportar guardias del mes",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_BLANCO
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            dialogo,
            text=f"{mes_texto} {anio}  ·  se exportará con los filtros activos en pantalla",
            font=("Segoe UI", 10),
            text_color="#64748B",
            fg_color=COLOR_BLANCO,
            wraplength=380
        ).pack(pady=(0, 18))

        btn_frame = ctk.CTkFrame(dialogo, fg_color=COLOR_BLANCO)
        btn_frame.pack(fill="x", padx=35)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        try:
            from ui.iconos import obtener_icono
            icono_pdf = obtener_icono("guardar_pdf", 42)
            icono_excel = obtener_icono("guardar_excel", 42)
        except Exception:
            icono_pdf = None
            icono_excel = None

        def cerrar_dialogo():
            if dialogo is not None and dialogo.winfo_exists():
                dialogo.destroy()

        def cmd_pdf():
            if dialogo is not None and dialogo.winfo_exists():
                dialogo.withdraw()
            try:
                exportar_guardias_mes_pdf(
                    anio, mes, guardias_por_dia,
                    cargo=cargo, especialidad=especialidad,
                    centro=centro, texto_busqueda=texto_busqueda,
                    parent_window=parent_window
                )
            finally:
                cerrar_dialogo()

        def cmd_excel():
            if dialogo is not None and dialogo.winfo_exists():
                dialogo.withdraw()
            try:
                exportar_guardias_mes_excel(
                    anio, mes, guardias_por_dia,
                    cargo=cargo, especialidad=especialidad,
                    centro=centro, texto_busqueda=texto_busqueda,
                    parent_window=parent_window
                )
            finally:
                cerrar_dialogo()

        btn_pdf = ctk.CTkButton(
            btn_frame,
            text="PDF",
            image=icono_pdf,
            compound="top" if icono_pdf else "left",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=COLOR_ROJO,
            hover_color="#B91C1C",
            corner_radius=10,
            cursor="hand2",
            width=150,
            height=125 if icono_pdf else 40,
            command=cmd_pdf
        )
        btn_pdf.grid(row=0, column=0, padx=(0, 10))

        btn_excel = ctk.CTkButton(
            btn_frame,
            text="Excel",
            image=icono_excel,
            compound="top" if icono_excel else "left",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=COLOR_VERDE,
            hover_color="#15803D",
            corner_radius=10,
            cursor="hand2",
            width=150,
            height=125 if icono_excel else 40,
            command=cmd_excel
        )
        btn_excel.grid(row=0, column=1, padx=(10, 0))

        return dialogo

    except Exception:
        if dialogo is not None and dialogo.winfo_exists():
            dialogo.destroy()
        raise