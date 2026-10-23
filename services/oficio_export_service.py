import sys
import re
import os
import base64
import mimetypes
import shutil
from datetime import datetime, date, timedelta
from tkinter import filedialog
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

from xhtml2pdf import pisa

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from ui.mensajes import mostrar_exito, mostrar_error
import win32com.client

# ==============================================================================
# EXPORTAR OFICIO A PDF
# ==============================================================================

def obtener_ruta_base():
    """
    Devuelve la carpeta raíz del proyecto.
    Funciona tanto ejecutando el .py como desde PyInstaller.
    """

    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)

        # Si el ejecutable está dentro de services/
        if os.path.isdir(os.path.join(base, "ui")):
            return base

        if os.path.isdir(os.path.join(os.path.dirname(base), "ui")):
            return os.path.dirname(base)

        return base

    # Este archivo está probablemente en:
    # Sistema_medicos_hospital/services/...
    #
    # Los logos están en:
    # Sistema_medicos_hospital/ui/Logos/

    carpeta_actual = os.path.dirname(
        os.path.abspath(__file__)
    )

    # Si ui existe al mismo nivel
    if os.path.isdir(
        os.path.join(carpeta_actual, "ui")
    ):
        return carpeta_actual

    # Si estamos dentro de services/
    carpeta_padre = os.path.dirname(
        carpeta_actual
    )

    if os.path.isdir(
        os.path.join(carpeta_padre, "ui")
    ):
        return carpeta_padre

    return carpeta_actual

def link_callback(uri, rel):
    """
    Callback requerido por xhtml2pdf/pisa para resolver rutas de
    imágenes (y otros recursos) referenciadas en el HTML con rutas
    relativas como 'ui/Logos/logo.png'.

    Sin esto, pisa intenta resolver la ruta contra el directorio de
    trabajo actual del proceso (os.getcwd()), que casi nunca coincide
    con la carpeta del proyecto/ejecutable, y las imágenes no aparecen
    en el PDF (sin lanzar ningún error).
    """

    # URLs remotas o data URIs: se dejan tal cual
    if uri.startswith("http://") or uri.startswith("https://") or uri.startswith("data:"):
        return uri

    # Si ya es una ruta absoluta que existe, se usa directamente
    if os.path.isabs(uri) and os.path.isfile(uri):
        return uri

    ruta_absoluta = os.path.join(obtener_ruta_base(), uri)

    if os.path.isfile(ruta_absoluta):
        return ruta_absoluta

    # Como último recurso, se prueba contra el directorio de trabajo
    # actual (comportamiento original de pisa)
    return uri

def exportar_oficio_pdf(oficio, parent_window=None):
    """
    Genera un PDF del oficio con el mismo encabezado (logos) y pie
    de página que la ficha del médico.
    """

    from tkinter import filedialog
    from xhtml2pdf import pisa
    from ui.mensajes import mostrar_exito, mostrar_error

    # Datos
    numero = getattr(oficio, "numero", None) or "—"
    destinatario = getattr(oficio, "destinatario", None) or "—"
    asunto = getattr(oficio, "asunto", None) or "—"
    observacion = getattr(oficio, "observacion", None)
    fecha = getattr(oficio, "fecha", None)

    # Formatear fecha
    if fecha:
        try:
            if hasattr(fecha, "strftime"):
                fecha_str = fecha.strftime("%d/%m/%Y")
            else:
                fecha_str = str(fecha)
        except Exception:
            fecha_str = str(fecha)
    else:
        fecha_str = "—"

    # Nombre de archivo limpio
    nombre_limpio = re.sub(
        r"[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ ]",
        "",
        str(numero)
    ).replace(" ", "_").upper() or "OFICIO"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Oficio en PDF",
        initialfile=f"Oficio_{nombre_limpio}.pdf",
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not filepath:
        return

    try:
        # Bloque de observación solo si existe
        observacion_html = ""
        if observacion and str(observacion).strip():
            observacion_html = f"""
            <div class="observacion-block">
                <span class="observacion-label">Observación:</span>
                <span class="observacion-texto">{str(observacion).strip()}</span>
            </div>
            """

        fecha_generacion = datetime.now().strftime("%d/%m/%Y %I:%M %p")

        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: letter;
                    margin: 10mm 12mm 50mm 12mm;
                    @frame footer {{
                        -pdf-frame-content: footer_content;
                        left: 12mm; right: 12mm; bottom: 0mm; height: 40mm;
                    }}
                }}

                * {{
                    box-sizing: border-box;
                }}

                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    color: #000000;
                    margin: 0;
                    padding: 0;
                    font-size: 11pt;
                    line-height: 1.35;
                }}

                .header-logos {{
                    width: 100%;
                    text-align: center;
                    border: none;
                    margin-bottom: 10px;
                }}

                .header-logos td {{
                    text-align: center;
                    vertical-align: middle;
                }}

                .header-logo-normal {{
                    height: 55px;
                }}

                .header-logo-salud {{
                    height: 150px;
                }}

                .header-logo-hospital {{
                    height: 95px;
                }}

                .header-logo-barrio {{
                    height: 40px;
                }}

                .doc-title {{
                    text-align: center;
                    font-size: 14pt;
                    font-weight: bold;
                    margin-bottom: 28px;
                    color: #000000;
                    margin-top: 18px;
                }}

                .oficio-numero {{
                    text-align: left;
                    font-size: 13pt;
                    font-weight: bold;
                    color: #000000;
                    margin-bottom: 18px;
                }}

                .destinatario-block {{
                    margin-bottom: 22px;
                }}

                .destinatario-label {{
                    font-weight: bold;
                    color: #333333;
                    font-size: 10pt;
                    display: block;
                    margin-bottom: 3px;
                }}

                .destinatario-valor {{
                    font-size: 11.5pt;
                    color: #000000;
                }}

                .asunto-parrafo {{
                    text-align: justify;
                    font-size: 11pt;
                    color: #000000;
                    margin-bottom: 22px;
                    line-height: 1.45;
                }}

                .observacion-block {{
                    margin-top: 8px;
                    margin-bottom: 10px;
                }}

                .observacion-label {{
                    font-weight: bold;
                    color: #333333;
                    font-size: 10.5pt;
                }}

                .observacion-texto {{
                    font-size: 10.5pt;
                    color: #000000;
                }}

                .fecha-oficio {{
                    text-align: right;
                    font-weight: bold;
                    font-size: 10pt;
                    color: #000000;
                    margin-bottom: 20px;
                }}

                #footer_content {{
                    width: 100%;
                }}

                .footer-table {{
                    width: 100%;
                    color: #000000;
                    text-align: center;
                    border-collapse: collapse;
                }}

                .footer-table td {{
                    vertical-align: middle;
                }}
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
                            width:60%;
                            text-align:center;
                            vertical-align:middle;
                            border-top:1px solid #000000;
                            padding-top: 0px;
                            font-size:8pt;
                            line-height:1.2;
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
                    <td>
                        <img src="ui/Logos/Logo-Min-Salud-2009.png"
                             class="header-logo-salud">
                    </td>
                    <td>
                        <img src="ui/Logos/logo.png"
                             class="header-logo-hospital">
                    </td>
                    <td>
                        <img src="ui/Logos/Barrio-adentro.png"
                             class="header-logo-barrio">
                    </td>
                    <td>
                        <img src="ui/Logos/spns.png"
                             class="header-logo-normal">
                    </td>
                    <td>
                        <img src="ui/Logos/cropped-Logo-Nuevo-Fondo-Blanco-1.png"
                             class="header-logo-normal">
                    </td>
                </tr>
            </table>

            <div class="doc-title">OFICIO</div>

            <div class="fecha-oficio">Fecha: {fecha_str}</div>

            <div class="oficio-numero">
                OFICIO NÚMERO: {numero}
            </div>

            <div class="destinatario-block">
                <span class="destinatario-label">Destinatario:</span>
                <span class="destinatario-valor">{destinatario}</span>
            </div>

            <div class="asunto-parrafo">
                {asunto}
            </div>

            {observacion_html}

            <div style="
                margin-top: 30px;
                text-align: right;
                font-size: 8pt;
                color: #666666;
                font-style: italic;
            ">
                Documento generado el {fecha_generacion}
            </div>
        </body>
        </html>
        """

        with open(filepath, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file,
                link_callback=link_callback   # la misma función que usas en la ficha médica
            )

        if pisa_status.err:
            mostrar_error(
                parent_window,
                "Error de exportación",
                "Hubo un problema al generar el PDF del oficio."
            )
        else:
            mostrar_exito(
                parent_window,
                "Exportación exitosa",
                "El oficio se generó correctamente."
            )

            # Abrir automáticamente en Windows (opcional)
            if os.name == "nt":
                os.startfile(filepath)

    except Exception as e:
        mostrar_error(
            parent_window,
            "Error de exportación",
            f"No se pudo generar el PDF del oficio:\n{str(e)}"
        )
        
