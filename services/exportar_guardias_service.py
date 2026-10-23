import os
import re
from datetime import datetime, date
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

from xhtml2pdf import pisa
import win32com.client
import shutil

from ui.mensajes import mostrar_exito, mostrar_error
from services.exportar_medico_service import link_callback, obtener_ruta_base, obtener_nombre_completo, valor_medico
from ui.Modulos.Medicos.colores import COLOR_BLANCO, COLOR_TEXTO, COLOR_ROJO, COLOR_VERDE

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def obtener_mes_texto(mes):
    meses = [
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
    ]
    return meses[mes - 1]

def formatear_fecha_letras(fecha_obj):
    if not isinstance(fecha_obj, (date, datetime)):
        return "FECHA NO VÁLIDA"
    
    dia = f"{fecha_obj.day:02d}"
    mes = obtener_mes_texto(fecha_obj.month)
    anio = fecha_obj.year
    
    return f"{dia} DE {mes} DE {anio}"

# ==============================================================================
# EXPORTAR GUARDIAS DEL DÍA A PDF
# ==============================================================================

def exportar_guardias_dia_pdf(fecha_obj, medicos_guardia, observaciones="", parent_window=None):
    
    fecha_letras = formatear_fecha_letras(fecha_obj)
    fecha_corta = fecha_obj.strftime("%d/%m/%Y")
    fecha_generacion = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    
    nombre_archivo = f"Reporte_Guardias_{fecha_obj.strftime('%Y%m%d')}.pdf"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Reporte de Guardias PDF",
        initialfile=nombre_archivo,
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not filepath:
        return

    # Construir las cajas de los médicos
    medicos_html = ""
    for medico in medicos_guardia:
        nombre = medico.get("nombre", "Sin nombre").upper()
        especialidad = medico.get("especialidad", "—")
        cargo = medico.get("cargo", "—")
        centro = medico.get("centro", "—")
        telefono = medico.get("telefono", "—")
        
        # Datos de inactividad / reposo
        esta_inactivo = medico.get("inactivo", False)
        causa_inactividad = medico.get("causa_inactividad", "").strip()
        
        prefijo = "DRA." if "Gineco" in especialidad or "Pediatra" in especialidad else "DR."
        
        box_class = "medico-box-inactivo" if esta_inactivo else "medico-box"
        
        estado_badge_html = ""
        if esta_inactivo:
            motivo = causa_inactividad if causa_inactividad else "Inactividad / Reposo registrado"
            estado_badge_html = f'''
            <div class="inactivo-badge">
                ⚠️ ESTADO: TENÍA GUARDIA ASIGNADA PERO ESTÁ DE REPOSO / INACTIVO ({motivo.upper()})
            </div>
            '''
        
        medicos_html += f'''
        <div class="{box_class}">
            <div class="medico-name">{prefijo} {nombre}</div>
            {estado_badge_html}
            <table class="medico-info">
                <tr>
                    <td style="width: 100px;"><strong>Especialidad:</strong></td>
                    <td>{especialidad}</td>
                </tr>
                <tr>
                    <td><strong>Cargo:</strong></td>
                    <td>{cargo}</td>
                </tr>
                <tr>
                    <td><strong>Centro:</strong></td>
                    <td>{centro}</td>
                </tr>
                <tr>
                    <td><strong>Teléfono:</strong></td>
                    <td>{telefono}</td>
                </tr>
            </table>
        </div>
        '''

    observaciones_html = ""
    if observaciones.strip():
        observaciones_html = f'''
        <div class="section-title">OBSERVACIONES</div>
        <div class="observaciones-box">
            {observaciones}
        </div>
        '''

    try:
        html_content = f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: letter;
                    margin: 10mm 12mm 45mm 12mm;
                    @frame footer {{
                        -pdf-frame-content: footer_content;
                        left: 12mm; right: 12mm; bottom: 0mm; height: 40mm;
                    }}
                }}
                
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    color: #000000;
                    margin: 0;
                    padding: 0;
                    font-size: 10pt;
                    line-height: 1.3;
                }}

                .header-logos {{
                    width: 100%;
                    text-align: center;
                    border: none;
                    margin-bottom: 15px;
                }}
                .header-logos td {{ text-align: center; vertical-align: middle; }}
                .header-logo-normal {{ height: 50px; }}
                .header-logo-salud {{ height: 130px; }}
                .header-logo-hospital {{ height: 85px; }}
                .header-logo-barrio {{ height: 35px; }}

                .title-container {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .hospital-title {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #000000;
                }}
                .report-title {{
                    font-size: 16pt;
                    font-weight: bold;
                    color: #000000;
                    margin-top: 5px;
                    margin-bottom: 5px;
                }}
                .date-title {{
                    font-size: 12pt;
                    font-weight: bold;
                    color: #555555;
                }}
                
                .separator {{
                    border-top: 2px solid #0F4C81;
                    margin-bottom: 20px;
                }}

                .section-title {{
                    font-size: 12pt;
                    font-weight: bold;
                    color: #0F4C81;
                    margin-bottom: 10px;
                    text-transform: uppercase;
                }}

                .medico-box {{
                    border: 1px solid #CBD5E1;
                    border-radius: 5px;
                    padding: 10px 15px;
                    margin-bottom: 12px;
                    background-color: #F8FAFC;
                }}

                .medico-box-inactivo {{
                    border: 1px solid #F59E0B;
                    border-radius: 5px;
                    padding: 10px 15px;
                    margin-bottom: 12px;
                    background-color: #FFFBEB;
                }}

                .inactivo-badge {{
                    background-color: #FEF3C7;
                    border: 1px solid #F59E0B;
                    color: #92400E;
                    padding: 5px 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 8.5pt;
                    margin-bottom: 8px;
                }}

                .medico-name {{
                    font-size: 11pt;
                    font-weight: bold;
                    color: #0F4C81;
                    margin-bottom: 6px;
                    padding-bottom: 4px;
                    border-bottom: 1px solid #E2E8F0;
                }}

                .medico-info {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .medico-info td {{
                    padding: 2px 0;
                    font-size: 10pt;
                    color: #333333;
                }}

                .observaciones-box {{
                    border: 1px dashed #94A3B8;
                    padding: 10px 15px;
                    background-color: #FFFFFF;
                    font-style: italic;
                    color: #333333;
                    margin-bottom: 20px;
                }}
                
                #footer_content {{ width: 100%; }}
                .footer-table {{ width: 100%; color: #000000; text-align: center; border-collapse: collapse; }}
                .footer-table td {{ vertical-align: middle; }}
            </style>
        </head>
        <body>
            <div id="footer_content">
                <table class="footer-table">
                    <tr>
                        <td style="width:20%; text-align:left; vertical-align:middle; line-height: 55px;">
                            <img src="ui/Logos/amemostachira.png" width="80">
                        </td>
                        <td style="
                            width:60%; text-align:center; vertical-align:middle;
                            border-top:1px solid #000000; padding-top: 0px; font-size:8pt; line-height:1.2;
                        ">
                            Final De Av. Manuel Pulido Méndez - Diagonal al IPAS ME - Rubio Municipio Junín<br/>
                            Correo: direcciondtto2hospitalderubio@gmail.com
                        </td>
                        <td style="width:20%; text-align:right; vertical-align:middle; line-height: 55px;">
                            <img src="ui/Logos/freddy_gobernador.png" width="80">
                        </td>
                    </tr>
                </table>
            </div>

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
                <div class="report-title">REPORTE DE GUARDIAS</div>
                <div class="date-title">{fecha_letras}</div>
            </div>

            <div class="separator"></div>

            <div class="section-title">MÉDICOS DE GUARDIA</div>
            
            {medicos_html}

            <br/>
            {observaciones_html}
            
            <div class="separator"></div>
            <div style="text-align: right; font-size: 9pt; color: #666666; font-style: italic;">
                Generado el: {fecha_generacion}
            </div>

        </body>
        </html>
        '''

        with open(filepath, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file,
                link_callback=link_callback
            )

        if pisa_status.err:
            mostrar_error(parent_window, "Error de exportación", "Hubo un problema al generar el PDF de las guardias.")
        else:
            mostrar_exito(parent_window, "Exportación exitosa", "El reporte de guardias se generó correctamente en PDF.")
            
            if os.name == 'nt':
                os.startfile(filepath)

    except Exception as e:
        mostrar_error(parent_window, "Error de exportación", f"No se pudo generar el PDF: {str(e)}")


# ==============================================================================
# EXPORTAR GUARDIAS DEL DÍA A EXCEL
# ==============================================================================

# ==============================================================================
# EXPORTAR GUARDIAS DEL DÍA A EXCEL (USANDO PLANTILLA REAL Y MOTOR DE EXCEL)
# ==============================================================================

def exportar_guardias_dia_excel(fecha_obj, medicos_guardia, observaciones="", parent_window=None):
    
    fecha_letras = formatear_fecha_letras(fecha_obj)
    nombre_archivo = f"Reporte_Guardias_{fecha_obj.strftime('%Y%m%d')}.xlsx"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Reporte de Guardias Excel",
        initialfile=nombre_archivo,
        defaultextension=".xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")]
    )

    if not filepath:
        return

    # Localizar plantilla
    ruta_base = obtener_ruta_base()
    ruta_plantilla = os.path.join(ruta_base, "plantillas", "Reporte_guardia_del_dia.xlsx")

    if not os.path.isfile(ruta_plantilla):
        mostrar_error(
            parent_window, 
            "Plantilla no encontrada", 
            f"No se encontró la plantilla en:\n{ruta_plantilla}"
        )
        return

    # Verificar disponibilidad de Excel
    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
    except Exception:
        mostrar_error(
            parent_window, 
            "Excel no detectado", 
            "Para exportar el reporte con formato completo es necesario tener instalado Microsoft Excel en este equipo."
        )
        return

    try:
        # Copiamos la plantilla a la ruta destino
        shutil.copy2(ruta_plantilla, filepath)

        excel.Visible = False
        excel.DisplayAlerts = False

        ruta_abs = os.path.abspath(filepath)
        wb = excel.Workbooks.Open(ruta_abs)

        try:
            ws = wb.Worksheets("Guardias")
        except Exception:
            try:
                ws = wb.Worksheets("Reporte Guardias")
            except Exception:
                ws = wb.Worksheets(1)

        # Constantes de Excel
        XL_MOVE_AND_SIZE = 1
        XL_SHIFT_UP = -4162
        XL_PASTE_FORMATS = -4122

        # Ajustar placement de formas e imágenes para preservar el diseño
        try:
            for forma in ws.Shapes:
                forma.Placement = XL_MOVE_AND_SIZE
        except Exception:
            pass

        # Constantes de diseño de la plantilla
        FILA_SUBTITULO = 6
        FILA_DATOS_INICIO = 9
        FILAS_PLANTILLA_ORIGINAL = 4
        FILA_ULTIMA_DATOS_PLANTILLA = FILA_DATOS_INICIO + FILAS_PLANTILLA_ORIGINAL - 1  # Fila 13

        total_guardias = len(medicos_guardia)

        # Inyectar subtítulo / fecha
        ws.Range(f"A{FILA_SUBTITULO}").Value = fecha_letras.upper()

        # Ajustar filas dinámicamente manteniendo bordes y estilos
        diferencia = total_guardias - FILAS_PLANTILLA_ORIGINAL

        if diferencia > 0:
            # Insertar filas adicionales y copiar formato
            fila_insercion = FILA_ULTIMA_DATOS_PLANTILLA + 1
            ws.Rows(f"{fila_insercion}:{fila_insercion + diferencia - 1}").Insert()
            ws.Rows(FILA_ULTIMA_DATOS_PLANTILLA).Copy()
            ws.Rows(f"{fila_insercion}:{fila_insercion + diferencia - 1}").PasteSpecial(
                Paste=XL_PASTE_FORMATS
            )
            excel.CutCopyMode = False

        elif diferencia < 0:
            # Eliminar filas sobrantes de la plantilla de ejemplo
            filas_a_eliminar = abs(diferencia)
            fila_desde = FILA_ULTIMA_DATOS_PLANTILLA - filas_a_eliminar + 1
            ws.Rows(f"{fila_desde}:{FILA_ULTIMA_DATOS_PLANTILLA}").Delete(Shift=XL_SHIFT_UP)

        # Inyectar médicos de guardia
        for i, medico in enumerate(medicos_guardia, start=1):
            fila_actual = FILA_DATOS_INICIO + i - 1

            esta_inactivo = medico.get("inactivo", False)
            causa_inactividad = medico.get("causa_inactividad", "").strip()

            nombre = medico.get("nombre", "—")
            especialidad = medico.get("especialidad", "—")
            cargo = medico.get("cargo", "—")
            centro = medico.get("centro", "—")
            telefono = medico.get("telefono", "—")

            if esta_inactivo:
                motivo = causa_inactividad if causa_inactividad else "Inactivo / Reposo"
                # Añadir la etiqueta de inactivo al lado del nombre
                nombre = f"{nombre} - INACTIVO ({motivo.upper()})"
                estatus_str = f"INACTIVO / REPOSO ({motivo.upper()})"
            else:
                estatus_str = "ACTIVO"

            # Asignar valores por celdas
            ws.Cells(fila_actual, 1).Value = i
            ws.Cells(fila_actual, 2).Value = nombre
            ws.Cells(fila_actual, 3).Value = especialidad
            ws.Cells(fila_actual, 4).Value = cargo
            ws.Cells(fila_actual, 5).Value = centro
            ws.Cells(fila_actual, 6).Value = telefono
            # ws.Cells(fila_actual, 7).Value = estatus_str  <-- ELIMINAR O COMENTAR ESTA LÍNEA

        # Escribir observaciones si existen
        fila_total = FILA_DATOS_INICIO + total_guardias
        if observaciones and observaciones.strip():
            fila_obs = fila_total + 2
            try:
                ws.Cells(fila_obs, 1).Value = f"OBSERVACIONES: {observaciones.strip()}"
            except Exception:
                pass

        wb.Save()
        wb.Close()

        mostrar_exito(parent_window, "Exportación exitosa", "El reporte de guardias se generó correctamente en Excel.")

        if os.name == 'nt':
            os.startfile(filepath)

    except Exception as e:
        mostrar_error(parent_window, "Error de exportación", f"No se pudo generar el Excel:\n{str(e)}")
    finally:
        if excel:
            excel.Quit()


# ==============================================================================
# VENTANA DE DIÁLOGO PARA SELECCIONAR FORMATO DE EXPORTACIÓN
# ==============================================================================

def mostrar_dialogo_exportar_guardias(fecha_obj, medicos_guardia, observaciones="", parent_window=None):
    dialogo = None

    try:
        dialogo = ctk.CTkToplevel(parent_window)
        dialogo.title("Exportar Guardias")
        dialogo.geometry("420x260")
        dialogo.resizable(False, False)
        dialogo.configure(fg_color=COLOR_BLANCO)

        if parent_window:
            dialogo.transient(parent_window)

        dialogo.grab_set()

        # Centrar diálogo
        dialogo.update_idletasks()

        if parent_window and parent_window.winfo_exists():
            x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (420 // 2)
            y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (260 // 2)
        else:
            x = (dialogo.winfo_screenwidth() // 2) - (420 // 2)
            y = (dialogo.winfo_screenheight() // 2) - (260 // 2)

        dialogo.geometry(f"420x260+{x}+{y}")

        ctk.CTkLabel(
            dialogo,
            text="Seleccione el formato de exportación",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_BLANCO
        ).pack(pady=(28, 22))

        btn_frame = ctk.CTkFrame(dialogo, fg_color=COLOR_BLANCO)
        btn_frame.pack(fill="x", padx=35)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        try:
            from ui.iconos import obtener_icono
            icono_pdf = obtener_icono("guardar_pdf", 42)
            icono_excel = obtener_icono("guardar_excel", 42)
        except:
            icono_pdf = None
            icono_excel = None

        def cerrar_dialogo():
            if dialogo is not None and dialogo.winfo_exists():
                dialogo.destroy()

        def cmd_pdf():
            if dialogo is not None and dialogo.winfo_exists():
                dialogo.withdraw()
            try:
                exportar_guardias_dia_pdf(fecha_obj, medicos_guardia, observaciones, parent_window)
            finally:
                cerrar_dialogo()

        def cmd_excel():
            if dialogo is not None and dialogo.winfo_exists():
                dialogo.withdraw()
            try:
                exportar_guardias_dia_excel(fecha_obj, medicos_guardia, observaciones, parent_window)
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