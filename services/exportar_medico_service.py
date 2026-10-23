import os
import re
import sys
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

try:
    from services.guardia_service import obtener_guardias_medico
except ImportError:
    # Ajusta la ruta según la estructura real de tu proyecto
    from guardia_service import obtener_guardias_medico


# ==============================================================================
# FUNCIONES AUXILIARES
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


def imagen_a_base64(ruta_relativa):
    """
    (No usado actualmente en el PDF; se deja disponible por si se
    necesita incrustar alguna imagen puntual en base64).
    """

    ruta_absoluta = os.path.join(obtener_ruta_base(), ruta_relativa)

    if not os.path.isfile(ruta_absoluta):
        return ""

    tipo_mime, _ = mimetypes.guess_type(ruta_absoluta)
    tipo_mime = tipo_mime or "image/png"

    try:
        with open(ruta_absoluta, "rb") as f:
            datos = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{tipo_mime};base64,{datos}"
    except Exception:
        return ""


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


def obtener_nombre_completo(medico):
    """
    Obtiene el nombre completo independientemente de si viene
    en 'nombre' o separado en nombres/apellidos.
    """

    nombre = medico.get("nombre")

    if nombre:
        return str(nombre).strip()

    nombres = medico.get("nombres", "") or ""
    apellidos = medico.get("apellidos", "") or ""

    return f"{nombres} {apellidos}".strip() or "SIN NOMBRE"


def valor_medico(medico, *claves, defecto="—"):
    """
    Busca un valor usando varias claves posibles.

    Ejemplo:
        valor_medico(medico, "centro_salud", "centro")
    """

    for clave in claves:

        valor = medico.get(clave)

        if valor is not None:

            if isinstance(valor, str):

                valor = valor.strip()

                if valor:
                    return valor

            else:
                return str(valor)

    return defecto


def formatear_fecha(valor, defecto="—"):
    """
    Convierte fechas provenientes de MySQL o Python
    al formato DD/MM/YYYY.
    """

    if valor is None:
        return defecto

    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")

    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")

    valor = str(valor).strip()

    if not valor:
        return defecto

    formatos = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y"
    ]

    for formato in formatos:

        try:

            fecha = datetime.strptime(valor, formato)

            return fecha.strftime("%d/%m/%Y")

        except ValueError:
            continue

    return valor


def obtener_frecuencia(medico):
    """
    Obtiene la frecuencia de guardia.
    Soporta valores como:
        3
        '3'
        'Cada 3 días'
    """

    frecuencia = medico.get("frecuencia_guardia")

    if frecuencia is None:
        return None

    texto = str(frecuencia).strip()

    if not texto:
        return None

    # Extraer el número aunque venga como "Cada 3 días"
    coincidencia = re.search(r"\d+", texto)

    if coincidencia:
        try:
            return int(coincidencia.group())
        except Exception:
            pass

    return None


# ==============================================================================
# CALCULAR ÚLTIMA Y PRÓXIMA GUARDIA
# ==============================================================================

def calcular_guardias(medico):
    """
    Calcula la última y la próxima guardia a partir de las guardias
    reales registradas en la tabla Guardia (ya no usa frecuencia).

    - Respeta períodos de inactividad (reposo / permiso).
    - Devuelve strings listos para mostrar en PDF/Excel.
    """
    id_medico = medico.get("id_medico")
    if not id_medico:
        return "—", "—"

    try:
        # 1. Obtener todas las guardias activas del médico
        guardias = obtener_guardias_medico(id_medico)
        if not guardias:
            return "—", "—"

        # Convertir a objetos date y ordenar
        fechas = sorted({
            g["fecha_guardia"]
            for g in guardias
            if g.get("fecha_guardia")
        })

        if not fechas:
            return "—", "—"

        # 2. Parsear fechas de inactividad
        def parsear_fecha(val):
            if not val:
                return None
            if isinstance(val, (datetime, date)):
                return val.date() if isinstance(val, datetime) else val
            txt = str(val).strip()
            if "T" in txt:
                txt = txt.split("T")[0]
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(txt, fmt).date()
                except ValueError:
                    continue
            return None

        inactivo_inicio = parsear_fecha(medico.get("fecha_inicio_inactividad"))
        inactivo_fin   = parsear_fecha(medico.get("fecha_fin_inactividad"))

        hoy = date.today()

        def esta_en_inactividad(f):
            if inactivo_inicio and inactivo_fin:
                return inactivo_inicio <= f <= inactivo_fin
            if inactivo_inicio and not inactivo_fin:
                return f >= inactivo_inicio
            if inactivo_fin and not inactivo_inicio:
                return f <= inactivo_fin
            return False

        # 3. Filtrar guardias que caen dentro de inactividad
        fechas_validas = [f for f in fechas if not esta_en_inactividad(f)]

        if not fechas_validas:
            return "—", "—"

        # 4. Última guardia = la más reciente que ya pasó (o es hoy)
        ultima_valida = None
        for f in reversed(fechas_validas):
            if f <= hoy:
                ultima_valida = f
                break

        # 5. Próxima guardia = la primera futura (o hoy)
        proxima_valida = None
        for f in fechas_validas:
            if f >= hoy:
                proxima_valida = f
                break

        # 6. Formatear
        str_ultima = (
            ultima_valida.strftime("%d/%m/%Y")
            if ultima_valida
            else "Aún no realizada"
        )

        if proxima_valida == hoy:
            str_proxima = hoy.strftime("%d/%m/%Y") + " (Hoy)"
        elif proxima_valida:
            str_proxima = proxima_valida.strftime("%d/%m/%Y")
        else:
            str_proxima = "—"

        return str_ultima, str_proxima

    except Exception:
        return "—", "—"


# ==============================================================================
# EXPORTAR MÉDICO A PDF
# ==============================================================================

def exportar_medico_pdf(medico, parent_window=None):

    nombre_completo = obtener_nombre_completo(medico)

    nombre_limpio = re.sub(
        r"[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ ]",
        "",
        nombre_completo
    ).replace(" ", "_").upper()

    if not nombre_limpio:
        nombre_limpio = "MEDICO"

    # DATOS
    nombre = nombre_completo.upper()
    cedula = valor_medico(medico, "cedula", defecto="—")
    codigo = valor_medico(medico, "codigo", defecto="—")
    nombres = valor_medico(medico, "nombres", defecto="—")
    apellidos = valor_medico(medico, "apellidos", defecto="—")
    telefono = valor_medico(medico, "telefono", defecto="—")
    correo = valor_medico(medico, "correo", defecto="—")
    cargo = valor_medico(medico, "cargo", defecto="—")
    especialidad = valor_medico(medico, "especialidad", defecto="—")
    dependencia = valor_medico(medico, "dependencia", defecto="—")
    contratacion = valor_medico(medico, "tipo_contratacion", "contratacion", defecto="—")
    fecha_ingreso = formatear_fecha(medico.get("fecha_ingreso"))
    centro_salud = valor_medico(medico, "centro_salud", "centro", defecto="—")
    asic = valor_medico(medico, "asic", defecto="—")
    tipologia = valor_medico(medico, "tipologia_centro", defecto="—")
    ubicacion_administrativa = valor_medico(medico, "ubicacion_administrativa", "ubicacion", defecto="—")
    formacion = valor_medico(medico, "formacion_estudiando", "formacion", defecto="No esta cursando ninguna formación académica")
    estatus = valor_medico(medico, "estatus", "estado", defecto="—").upper()

    # GUARDIAS (ya no se usa frecuencia)
    ultima_guardia, proxima_guardia = calcular_guardias(medico)

    # ESTADO INACTIVIDAD SI APLICA
    causa_inactividad = valor_medico(medico, "causa_inactividad", defecto="—")
    fecha_inicio_inactividad = formatear_fecha(medico.get("fecha_inicio_inactividad"))
    fecha_fin_inactividad = formatear_fecha(medico.get("fecha_fin_inactividad"))
    tiempo_inactividad = valor_medico(medico, "tiempo_inactividad", defecto="—")

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Ficha del Médico en PDF",
        initialfile=f"Ficha_Medico_{nombre_limpio}.pdf",
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not filepath:
        return

    try:
        estado_html = ""
        if estatus == "INACTIVO":
            estado_html = f"""
            <div class="section-box">
                <div class="section-title">ESTADO DEL MÉDICO</div>
                <table class="data-table">
                    <tr>
                        <td class="border-right"><span class="label">Estatus:</span> <span class="value">{estatus}</span></td>
                        <td><span class="label">Causa de inactividad:</span> <span class="value">{causa_inactividad}</span></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Fecha inicio inactividad:</span> <span class="value">{fecha_inicio_inactividad}</span></td>
                        <td><span class="label">Fecha fin inactividad:</span> <span class="value">{fecha_fin_inactividad}</span></td>
                    </tr>
                    <tr>
                        <td colspan="2"><span class="label">Tiempo de inactividad:</span> <span class="value">{tiempo_inactividad}</span></td>
                    </tr>
                </table>
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
                    font-size: 9.5pt;
                    line-height: 1.2;
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
                    margin-bottom: 22px;
                    color: #000000;
                    margin-top: 20px;
    
                }}

                .header {{
                    margin-bottom: 10px;
                }}

                .header-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}

                .header-left {{
                    padding: 8px 12px;
                    vertical-align: middle;
                }}

                

                .header-title {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #FFFFFF;
                    letter-spacing: 0.5px;
                    margin: 0 !important;
                    padding: 0 !important;
                    line-height: 1.1;
                }}

                .header-subtitle {{
                    font-size: 9pt;
                    color: #FFFFFF;
                    margin: 2px 0 0 0 !important; 
                    padding: 0 !important;
                    line-height: 1.1;
                }}

                
                 

                .section-box {{
                    border: 1px solid #b0bec5;
                    border-radius: 4px;
                    margin-bottom: 8px;
                    padding: 6px 8px;
                    background-color: #ffffff;
                }}

                .section-title {{
                    color: #0F4C81;
                    font-size: 9.5pt;
                    font-weight: bold;
                    text-transform: uppercase;
                    padding-bottom: 4px;
                    margin-bottom: 4px;
                    border-bottom: 1px solid #b0bec5;
                }}

                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}

                .data-table td {{
                    padding: 3px 4px;
                    vertical-align: top;
                    width: 50%;
                    border-bottom: 1px solid #f0f0f0;
                }}

                .data-table tr:last-child td {{
                    border-bottom: none;
                }}

                .data-table td.border-right {{
                    border-right: 1px solid #e0e0e0;
                }}

                .label {{
                    font-weight: bold;
                    color: #333333;
                    font-size: 8.5pt;
                    display: inline-block;
                    width: 135px;
                }}

                .value {{
                    color: #000000;
                    font-size: 9pt;
                }}

                .proxima-box {{
                    border: 1px solid #d0d7de;
                    background-color: #f4f7fa;
                    padding: 6px 10px;
                    margin-top: 4px;
                    border-radius: 3px;
                }}

                .proxima-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}

                .proxima-title {{
                    font-weight: bold;
                    color: #0F4C81;
                    font-size: 9.5pt;
                }}

                .proxima-fecha {{
                    font-weight: bold;
                    color: #000000;
                    font-size: 10.5pt;
                    text-align: right;
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

            <div class="doc-title">FICHA ADMINISTRATIVA PERSONAL MÉDICO</div>

            <div class="header">
                <table class="header-table" bgcolor="#2563EB">
                    <tr bgcolor="#2563EB">
                        <td class="header-left" bgcolor="#2563EB">
                            <div class="header-title">DR. {nombre}</div>
                            <div class="header-subtitle">
                                {cargo.upper()} &nbsp;&bull;&nbsp; C.I.: {cedula}
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <div class="section-box">
                <div class="section-title">INFORMACIÓN PERSONAL</div>
                <table class="data-table">
                    <tr>
                        <td class="border-right"><span class="label">Cédula:</span> <span class="value">{cedula}</span></td>
                        <td><span class="label">Teléfono:</span> <span class="value">{telefono}</span></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Código:</span> <span class="value">{codigo}</span></td>
                        <td><span class="label">Correo:</span> <span class="value">{correo}</span></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Nombres:</span> <span class="value">{nombres}</span></td>
                        <td></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Apellidos:</span> <span class="value">{apellidos}</span></td>
                        <td></td>
                    </tr>
                </table>
            </div>

            <div class="section-box">
                <div class="section-title">INFORMACIÓN PROFESIONAL Y UBICACIÓN</div>
                <table class="data-table">
                    <tr>
                        <td class="border-right"><span class="label">Fecha de Ingreso:</span> <span class="value">{fecha_ingreso}</span></td>
                        <td><span class="label">Centro de Salud:</span> <span class="value">{centro_salud}</span></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Cargo:</span> <span class="value">{cargo}</span></td>
                        <td><span class="label">ASIC:</span> <span class="value">{asic}</span></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Especialidad:</span> <span class="value">{especialidad}</span></td>
                        <td><span class="label">Tipología Centro:</span> <span class="value">{tipologia}</span></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Dependencia:</span> <span class="value">{dependencia}</span></td>
                        <td><span class="label">Ubicación Adm.:</span> <span class="value">{ubicacion_administrativa}</span></td>
                    </tr>
                    <tr>
                        <td class="border-right"><span class="label">Contratación:</span> <span class="value">{contratacion}</span></td>
                        <td><span class="label">Estatus:</span> <span class="value">{estatus}</span></td>
                    </tr>
                    <tr>
                        <td colspan="2"><span class="label">Formación Académica:</span> <span class="value">{formacion}</span></td>
                    </tr>
                </table>
            </div>

            <div class="section-box">
                <div class="section-title">PLANIFICACIÓN Y CONTROL DE GUARDIAS</div>
                <table class="data-table" style="margin-bottom: 6px;">
                    <tr>
                        <td class="border-right">
                            <span class="label">Última Guardia:</span>
                            <span class="value">{ultima_guardia}</span>
                        </td>
                        <td></td>
                    </tr>
                </table>

                <div class="proxima-box">
                    <table class="proxima-table">
                        <tr>
                            <td class="proxima-title">PRÓXIMA GUARDIA PROGRAMADA:</td>
                            <td class="proxima-fecha">{proxima_guardia}</td>
                        </tr>
                    </table>
                </div>
            </div>

            {estado_html}
            
        <div style="
            margin-top: 12px;
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
                link_callback=link_callback
            )

        if pisa_status.err:
            mostrar_error(parent_window, "Error de exportación", "Hubo un problema al generar el PDF.")
        else:
            mostrar_exito(parent_window, "Exportación exitosa", "La ficha del médico se generó correctamente.")

    except Exception as e:
        mostrar_error(parent_window, "Error de exportación", f"No se pudo generar el PDF:\n{str(e)}")



# ==============================================================================
# EXPORTAR MÉDICO A EXCEL - USANDO PLANTILLA
# ==============================================================================



def exportar_medico_excel(medico, parent_window=None):
    # ==========================================================================
    # DATOS DEL MÉDICO
    # ==========================================================================
    nombre_completo = obtener_nombre_completo(medico)
    nombre_limpio = re.sub(r"[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ ]", "", nombre_completo).replace(" ", "_").upper() or "MEDICO"
    nombre = nombre_completo.upper()

    cedula = valor_medico(medico, "cedula", defecto="—")
    codigo = valor_medico(medico, "codigo", defecto="—")
    nombres = valor_medico(medico, "nombres", defecto="—")
    apellidos = valor_medico(medico, "apellidos", defecto="—")
    telefono = valor_medico(medico, "telefono", defecto="—")
    correo = valor_medico(medico, "correo", defecto="—")
    cargo = valor_medico(medico, "cargo", defecto="—")
    especialidad = valor_medico(medico, "especialidad", defecto="—")
    dependencia = valor_medico(medico, "dependencia", defecto="—")
    contratacion = valor_medico(medico, "tipo_contratacion", "contratacion", defecto="—")
    fecha_ingreso = formatear_fecha(medico.get("fecha_ingreso"))
    centro_salud = valor_medico(medico, "centro_salud", "centro", defecto="—")
    asic = valor_medico(medico, "asic", defecto="—")
    tipologia = valor_medico(medico, "tipologia_centro", defecto="—")
    ubicacion_administrativa = valor_medico(medico, "ubicacion_administrativa", "ubicacion", defecto="—")
    formacion = valor_medico(medico, "formacion_estudiando", "formacion", defecto="No esta cursando ninguna formación académica")
    estatus = valor_medico(medico, "estatus", "estado", defecto="—").upper()

    # GUARDIAS E INACTIVIDAD (ya no se usa frecuencia)
    ultima_guardia, proxima_guardia = calcular_guardias(medico)

    causa_inactividad = valor_medico(medico, "causa_inactividad", defecto="—")
    fecha_inicio_inactividad = formatear_fecha(medico.get("fecha_inicio_inactividad"))
    fecha_fin_inactividad = formatear_fecha(medico.get("fecha_fin_inactividad"))
    tiempo_inactividad = valor_medico(medico, "tiempo_inactividad", defecto="—")

    fecha_generacion = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    # ==========================================================================
    # LOCALIZAR PLANTILLA Y RUTA DE DESTINO
    # ==========================================================================
    ruta_base = obtener_ruta_base()
    ruta_plantilla = os.path.join(ruta_base, "plantillas", "EJEMPLO.xlsx")

    if not os.path.isfile(ruta_plantilla):
        mostrar_error(parent_window, "Plantilla no encontrada", f"No se encontró la plantilla en:\n{ruta_plantilla}")
        return

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Ficha del Médico en Excel",
        initialfile=f"Ficha_Medico_{nombre_limpio}.xlsx",
        defaultextension=".xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")]
    )

    if not filepath:
        return

    # ==========================================================================
    # VERIFICAR DISPONIBILIDAD DE EXCEL
    # ==========================================================================
    try:
        excel = win32com.client.Dispatch("Excel.Application")
    except Exception:
        mostrar_error(
            parent_window, 
            "Excel no detectado", 
            "Para exportar la ficha con formato completo es necesario tener instalado Microsoft Excel en este equipo."
        )
        return

    # ==========================================================================
    # EDICIÓN MEDIANTE MOTOR DE EXCEL
    # ==========================================================================
    try:
        # Copiamos la plantilla al destino
        shutil.copy2(ruta_plantilla, filepath)

        # Configuramos Excel en segundo plano
        excel.Visible = False
        excel.DisplayAlerts = False

        # Abrimos el archivo copiado usando la ruta absoluta
        ruta_abs = os.path.abspath(filepath)
        wb = excel.Workbooks.Open(ruta_abs)
        
        # Seleccionamos la hoja
        try:
            ws = wb.Worksheets("Ficha Médico")
        except Exception:
            ws = wb.Worksheets(1)

        # INYECCIÓN DE DATOS (Mantiene el 100% del estilo de la plantilla)
        ws.Range("A5").Value = f"DR. {nombre}"
        ws.Range("F5").Value = estatus
        ws.Range("A6").Value = f"{cargo.upper()}   •   C.I.: {cedula}"
        ws.Range("D6").Value = f"Fecha de exportación: {fecha_generacion}"

        # INFORMACIÓN PERSONAL
        ws.Range("B8").Value = cedula
        ws.Range("D8").Value = codigo
        ws.Range("B9").Value = nombres
        ws.Range("D9").Value = apellidos
        ws.Range("B10").Value = telefono
        ws.Range("D10").Value = correo

        # INFORMACIÓN PROFESIONAL Y UBICACIÓN
        ws.Range("B12").Value = fecha_ingreso
        ws.Range("D12").Value = cargo
        ws.Range("B13").Value = especialidad
        ws.Range("D13").Value = dependencia
        ws.Range("B14").Value = contratacion
        ws.Range("D14").Value = centro_salud
        ws.Range("B15").Value = asic
        ws.Range("D15").Value = tipologia
        ws.Range("B16").Value = ubicacion_administrativa
        ws.Range("D16").Value = estatus

        # FORMACIÓN ACADÉMICA
        ws.Range("B17").Value = formacion

        # GUARDIAS (solo última y próxima; la frecuencia ya no se utiliza)
        ws.Range("B19").Value = f"'{ultima_guardia}" if ultima_guardia != "—" else ultima_guardia
        ws.Range("E20").Value = f"'{proxima_guardia}" if proxima_guardia != "—" else proxima_guardia

        # ESTADO DEL MÉDICO
        if estatus == "INACTIVO":
            # Asegurar que la sección esté visible
            ws.Rows("21:24").EntireRow.Hidden = False

            # Inyectar datos de inactividad
            ws.Range("B22").Value = estatus
            ws.Range("D22").Value = causa_inactividad
            ws.Range("B23").Value = fecha_inicio_inactividad
            ws.Range("D23").Value = fecha_fin_inactividad
            ws.Range("B24").Value = tiempo_inactividad
        else:
            # Ocultar completamente el bloque (Encabezado + Filas de datos)
            ws.Rows("21:24").EntireRow.Hidden = True

        # Guardar y cerrar
        wb.Save()
        wb.Close()

        mostrar_exito(parent_window, "Exportación exitosa", "La ficha del médico se generó correctamente.")

    except Exception as e:
        mostrar_error(parent_window, "Error de exportación", f"No se pudo generar el Excel:\n{str(e)}")
    finally:
        if excel:
            excel.Quit()
            

#Exportar lsita de medicos
def construir_subtitulo_filtros(filtros_aplicados):
    """
    Arma un subtítulo legible a partir de los filtros aplicados
    en la lista de médicos.

    Soporta dos formas de recibir 'filtros_aplicados':
      1) Una lista/tupla de textos ya armados, por ejemplo:
         ["Cargo: Artículo 8", "Estatus: Activo"]
         -> se unen con " | "

      2) Un diccionario, por ejemplo:
         {"cargo": "ARTICULO 8", "estatus": "ACTIVO", "es_rural": True}
         -> se convierte cada clave/valor en un texto "Etiqueta: Valor"

    NOTA: Este es un formateo genérico ("Cargo: Artículo 8 | Estatus: Activo").
    Si se necesita una frase más natural como "MÉDICOS ARTÍCULO 8 ACTIVOS",
    hay que decirme exactamente cómo se arma 'filtros_aplicados' en la
    pantalla de filtros para mapear cada combinación a esa frase.
    """

    if not filtros_aplicados:
        return "Todos los médicos registrados"

    partes = []

    if isinstance(filtros_aplicados, dict):

        for clave, valor in filtros_aplicados.items():

            if valor is None:
                continue

            if isinstance(valor, str) and not valor.strip():
                continue

            if isinstance(valor, bool):
                if valor:
                    etiqueta = str(clave).replace("_", " ").strip().capitalize()
                    partes.append(etiqueta)
                continue

            etiqueta = str(clave).replace("_", " ").strip().capitalize()
            partes.append(f"{etiqueta}: {valor}")

    elif isinstance(filtros_aplicados, (list, tuple, set)):

        for valor in filtros_aplicados:

            if valor is None:
                continue

            texto = str(valor).strip()

            if texto:
                partes.append(texto)

    else:
        texto = str(filtros_aplicados).strip()
        if texto:
            partes.append(texto)

    if not partes:
        return "Todos los médicos registrados"

    return " | ".join(partes)


def exportar_lista_medicos_pdf(medicos, filtros_aplicados, parent_window=None):
    """
    Exporta una lista de médicos a un archivo PDF en formato apaisado (Landscape),
    con las columnas de datos en una tabla ajustada para evitar desbordamientos.
    (Ya no incluye la columna de frecuencia de guardia.)
    """
    
    # 1. Solicitar ruta donde guardar
    ruta_guardado = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Reporte de Médicos PDF",
        initialfile=f"Reporte_Medicos_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not ruta_guardado:
        return

    # 1.1 Armar subtítulo dinámico según los filtros aplicados
    subtitulo_filtros = construir_subtitulo_filtros(filtros_aplicados)

    # 2. Generar el contenido de las filas dinámicamente
    filas_html = ""
    for i, medico in enumerate(medicos, start=1):
        
        # Procesar datos
        ultima_guardia, _ = calcular_guardias(medico)

        cedula = valor_medico(medico, "cedula")
        codigo = valor_medico(medico, "codigo")
        nombres = valor_medico(medico, "nombres")
        apellidos = valor_medico(medico, "apellidos")
        telefono = valor_medico(medico, "telefono")
        correo = valor_medico(medico, "correo")
        fecha_ingreso = formatear_fecha(valor_medico(medico, "fecha_ingreso", defecto=None))
        cargo = valor_medico(medico, "cargo")
        especialidad = valor_medico(medico, "especialidad")
        dependencia = valor_medico(medico, "dependencia")
        contratacion = valor_medico(medico, "tipo_contratacion", "contratacion")
        centro = valor_medico(medico, "centro_salud", "centro")
        asic = valor_medico(medico, "asic")
        tipologia = valor_medico(medico, "tipologia_centro")
        ubic_adm = valor_medico(medico, "ubicacion_administrativa", "ubicacion")
        estatus = valor_medico(medico, "estatus")
        causa_inact = valor_medico(medico, "causa_inactividad")
        
        # Corrección: Extraer directamente con medico.get() para no romper el objeto fecha
        inicio_inact = formatear_fecha(medico.get("fecha_inicio_inactividad"))
        fin_inact = formatear_fecha(medico.get("fecha_fin_inactividad"))
        tiempo_inact = valor_medico(medico, "tiempo_inactividad", defecto="—")
        
        formacion = valor_medico(medico, "formacion_estudiando", "formacion")

        clase_fila = "row-alt" if i % 2 == 0 else ""

        filas_html += f"""
        <tr class="{clase_fila}">
            <td>{i}</td>
            <td>{cedula}</td>
            <td>{codigo}</td>
            <td>{nombres}</td>
            <td>{apellidos}</td>
            <td>{telefono}</td>
            <td>{correo}</td>
            <td>{fecha_ingreso}</td>
            <td>{cargo}</td>
            <td>{especialidad}</td>
            <td>{dependencia}</td>
            <td>{contratacion}</td>
            <td>{centro}</td>
            <td>{asic}</td>
            <td>{tipologia}</td>
            <td>{ubic_adm}</td>
            <td>{estatus}</td>
            <td>{causa_inact}</td>
            <td>{inicio_inact}</td>
            <td>{fin_inact}</td>
            <td>{tiempo_inact}</td>
            <td>{formacion}</td>
            <td>{ultima_guardia}</td>
        </tr>
        """

    # 3. Construir la estructura completa del documento HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: letter landscape;
                margin: 5mm 5mm 22mm 5mm; /* Se deja espacio abajo para el pie de página repetido */
                @frame footer {{
                    -pdf-frame-content: footer_content;
                    left: 5mm; right: 5mm; bottom: 0mm; height: 20mm;
                }}
            }}
            
            body {{
                font-family: Arial, Helvetica, sans-serif;
                color: #000000;
                font-size: 4.5pt; /* Letra pequeña para caber todas las columnas */
            }}

            .subtitulo-filtros {{
                text-align: center;
                font-size: 7.5pt;
                font-weight: bold;
                color: #0F4C81;
                margin-top: -6px;
                margin-bottom: 8px;
                text-transform: uppercase;
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

            .header-logos {{
                width: 100%;
                text-align: center;
                border: none;
                margin-bottom: 10px;
            }}
            .header-logos td {{ border: none; text-align: center; vertical-align: middle; }}
            .header-logo-normal {{ height: 40px; }}
            .header-logo-salud {{ height: 60px; }}
            .header-logo-hospital {{ height: 80px; }}
            .header-logo-barrio {{ height: 30px; }}

            .doc-title {{
                text-align: center;
                font-size: 10pt;
                font-weight: bold;
                margin-bottom: 10px;
                color: #000000;
            }}

            .data-table {{
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed; /* Obliga a respetar los porcentajes de ancho y evita que se desborde */
            }}
            
            .data-table th, .data-table td {{
                border: 0.5px solid #546e7a;
                padding: 2px 1px; /* Relleno mínimo */
                text-align: center;
                vertical-align: middle;
                word-wrap: break-word; /* Fuerza el salto de línea en palabras largas como correos */
            }}
            
            

            .data-table th {{
                background-color: #DCE6F1;
                color: #000000;
                font-weight: bold;
                font-size: 4.5pt;
            }}
            
            .row-alt {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>

        <div id="footer_content">
            <table class="footer-table">
                <tr>
                    <td style="width:20%; text-align:left; vertical-align:middle; line-height: 40px;">
                        <img src="ui/Logos/amemostachira.png" width="60">
                    </td>
                    <td style="
                        width:60%;
                        text-align:center;
                        vertical-align:middle;
                        border-top:1px solid #000000;
                        padding-top: 0px;
                        font-size:6pt;
                        line-height:1.2;
                    ">
                        Final De Av. Manuel Pulido Méndez - Diagonal al IPAS ME - Rubio Municipio Junín<br/>
                        Correo: direcciondtto2hospitalderubio@gmail.com
                    </td>
                    <td style="width:20%; text-align:right; vertical-align:middle; line-height: 40px;">
                        <img src="ui/Logos/freddy_gobernador.png" width="60">
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

        <div class="doc-title">REPORTE GENERAL DE PERSONAL MÉDICO</div>
        <div class="subtitulo-filtros">{subtitulo_filtros}</div>

        <table class="data-table">
            <thead>
                <tr>
                    <th style="width: 1%;">N°</th>
                    <th style="width: 4%;">Cédula</th>
                    <th style="width: 3%;">Código</th>
                    <th style="width: 5%;">Nombres</th>
                    <th style="width: 5%;">Apellidos</th>
                    <th style="width: 4%;">Teléfono</th>
                    <th style="width: 8%;">Correo</th>
                    <th style="width: 3%;">F. Ingreso</th>
                    <th style="width: 4%;">Cargo</th>
                    <th style="width: 7%;">Especialidad</th>
                    <th style="width: 5%;">Dependencia</th>
                    <th style="width: 4%;">Contratación</th>
                    <th style="width: 5%;">Centro Salud</th>
                    <th style="width: 4%;">ASIC</th>
                    <th style="width: 3%;">Tipología</th>
                    <th style="width: 4%;">Ubic. Adm.</th>
                    <th style="width: 3%;">Estatus</th>
                    <th style="width: 4%;">Causa Inact.</th>
                    <th style="width: 4%;">Inicio Inact.</th>
                    <th style="width: 3%;">Fin Inact.</th>
                    <th style="width: 4%;">Tiempo Inact.</th>
                    <th style="width: 4%;">Formación</th>
                    <th style="width: 5%;">F. Últ. Gua.</th>
                </tr>
            </thead>
            <tbody>
                {filas_html}
            </tbody>
        </table>
        
        <div style="margin-top: 10px; font-size: 5pt; text-align: right; color: #555;">
            Total de médicos exportados: {len(medicos)} | Generado el: {datetime.now().strftime("%d/%m/%Y")}
        </div>
    </body>
    </html>
    """

    # 4. Generar el PDF
    try:
        with open(ruta_guardado, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file,
                link_callback=link_callback
            )

        if pisa_status.err:
            if parent_window:
                mostrar_error(parent_window, "Error", "Ocurrió un problema al generar el archivo PDF.")
        else:
            if parent_window:
                mostrar_exito(parent_window, "Éxito", f"El reporte PDF ha sido generado correctamente")

            if os.name == 'nt':
                os.startfile(ruta_guardado)

    except Exception as e:
        if parent_window:
            mostrar_error(parent_window, "Error inesperado", f"Ocurrió un error: {str(e)}")
            
# ==============================================================================
# EXPORTAR LISTA DE MÉDICOS A EXCEL (CON PLANTILLA REAL, MOTOR DE EXCEL)
# ==============================================================================

def exportar_lista_medicos_excel(medicos, filtros_aplicados, parent_window=None):
    """
    Exporta la lista de médicos a un archivo Excel (.xlsx) usando la
    plantilla 'Plantilla_listar_medicos.xlsx' y el motor real de Excel
    (win32com), igual que se hace en exportar_medico_excel() para la
    ficha individual.

    NO se reconstruye el Excel por código (no más openpyxl para esto):
    se abre la plantilla con Excel, se conserva el 100% de su estilo,
    bordes y estructura, y solo se:

        - Escribe el subtítulo con los filtros aplicados.
        - Inserta filas adicionales (copiando el formato de la última
          fila de datos) si hay más médicos que filas de ejemplo en
          la plantilla.
        - Elimina filas sobrantes si hay menos médicos que filas de
          ejemplo en la plantilla.
        - Vuelca los datos de cada médico en su fila correspondiente.
        - Actualiza la fila de totales (que se desplaza automáticamente
          junto con el resto del bloque inferior: fila en blanco,
          recuadro de dirección/sello, etc.).

    Estructura esperada de la plantilla (hoja "Reporte Médicos"):
        Fila 5  -> Título (merge A5:X5)
        Fila 6  -> Subtítulo / filtros (merge A6:X6)
        Fila 8  -> Encabezados de columna (A..X)
        Fila 9  -> Primera fila de datos de ejemplo
        Fila 13 -> Última fila de datos de ejemplo (5 filas de muestra)
        Fila 14 -> "Total de médicos exportados..." (se desplaza)
        Fila 16 -> Recuadro con dirección / logo (se desplaza)
    """

    # --------------------------------------------------------------------
    # CONSTANTES DE LA PLANTILLA (posiciones fijas del diseño)
    # --------------------------------------------------------------------
    FILA_SUBTITULO = 6
    FILA_ENCABEZADOS = 8
    FILA_DATOS_INICIO = 9
    FILAS_PLANTILLA_ORIGINAL = 5
    FILA_ULTIMA_DATOS_PLANTILLA = FILA_DATOS_INICIO + FILAS_PLANTILLA_ORIGINAL - 1  # 13

    # Constantes nativas de Excel (evitamos depender de win32com.constants)
    XL_SHIFT_UP = -4162
    XL_PASTE_FORMATS = -4122
    XL_MOVE_AND_SIZE = 1  # Placement de imágenes/formas: se mueven y
                           # redimensionan junto con las celdas.

    # Columnas de "fecha" que Excel tiende a reinterpretar/reformatear
    # automáticamente si se les asigna un texto con pinta de fecha.
    # Se protegen con un apóstrofe inicial, igual que se hace en
    # exportar_medico_excel() con las guardias.
    # (La columna de frecuencia ya no existe en la plantilla.)
    COLUMNAS_FECHA = {8, 19, 20, 23}  # H=F.Ingreso, S=Inicio Inact.,
                                       # T=Fin Inact., W=F. Últ. Gua.

    subtitulo_filtros = construir_subtitulo_filtros(filtros_aplicados)
    total_medicos = len(medicos)

    # --------------------------------------------------------------------
    # 1. Solicitar ruta donde guardar
    # --------------------------------------------------------------------
    ruta_guardado = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar Reporte de Médicos en Excel",
        initialfile=f"Reporte_Medicos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        defaultextension=".xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")]
    )

    if not ruta_guardado:
        return

    # --------------------------------------------------------------------
    # 2. Localizar la plantilla
    # --------------------------------------------------------------------
    ruta_base = obtener_ruta_base()
    ruta_plantilla = os.path.join(ruta_base, "plantillas", "Plantilla_listar_medicos.xlsx")

    if not os.path.isfile(ruta_plantilla):
        mostrar_error(
            parent_window,
            "Plantilla no encontrada",
            f"No se encontró la plantilla en:\n{ruta_plantilla}"
        )
        return

    # --------------------------------------------------------------------
    # 3. Verificar disponibilidad de Excel
    # --------------------------------------------------------------------
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

    # --------------------------------------------------------------------
    # 4. Edición mediante el motor de Excel (mantiene el 100% del estilo)
    # --------------------------------------------------------------------
    try:
        # Copiamos la plantilla al destino
        shutil.copy2(ruta_plantilla, ruta_guardado)

        excel.Visible = False
        excel.DisplayAlerts = False

        ruta_abs = os.path.abspath(ruta_guardado)
        wb = excel.Workbooks.Open(ruta_abs)

        try:
            ws = wb.Worksheets("Reporte Médicos")
        except Exception:
            ws = wb.Worksheets(1)

        # Nos aseguramos de que imágenes/logos se muevan y ajusten junto
        # con las filas al insertar/eliminar (para no romper el diseño).
        try:
            for forma in ws.Shapes:
                forma.Placement = XL_MOVE_AND_SIZE
        except Exception:
            pass

        # ------------------------------------------------------------
        # AJUSTAR CANTIDAD DE FILAS SEGÚN LA CANTIDAD DE MÉDICOS
        # ------------------------------------------------------------
        diferencia = total_medicos - FILAS_PLANTILLA_ORIGINAL

        if diferencia > 0:
            # Faltan filas: se insertan justo después de la última fila
            # de datos de la plantilla, copiando su formato (bordes,
            # fuente, relleno, alto de fila, etc.) para que las filas
            # nuevas luzcan idénticas a las existentes.
            fila_insercion = FILA_ULTIMA_DATOS_PLANTILLA + 1

            ws.Rows(f"{fila_insercion}:{fila_insercion + diferencia - 1}").Insert()

            ws.Rows(FILA_ULTIMA_DATOS_PLANTILLA).Copy()
            ws.Rows(f"{fila_insercion}:{fila_insercion + diferencia - 1}").PasteSpecial(
                Paste=XL_PASTE_FORMATS
            )
            excel.CutCopyMode = False

        elif diferencia < 0:
            # Sobran filas de ejemplo: se eliminan desde el final del
            # bloque de datos hacia arriba, conservando intactas las
            # primeras filas (con su formato original).
            filas_a_eliminar = abs(diferencia)
            fila_desde = FILA_ULTIMA_DATOS_PLANTILLA - filas_a_eliminar + 1

            ws.Rows(f"{fila_desde}:{FILA_ULTIMA_DATOS_PLANTILLA}").Delete(Shift=XL_SHIFT_UP)

        # A partir de aquí, la fila de totales y todo lo que está debajo
        # (fila en blanco, recuadro de dirección/logo) ya quedaron
        # desplazados automáticamente por Excel.
        fila_total = FILA_DATOS_INICIO + total_medicos

        # ------------------------------------------------------------
        # SUBTÍTULO (filtros aplicados)
        # ------------------------------------------------------------
        ws.Range(f"A{FILA_SUBTITULO}").Value = subtitulo_filtros.upper()

        # ------------------------------------------------------------
        # FILAS DE DATOS
        # ------------------------------------------------------------
        for i, medico in enumerate(medicos, start=1):

            fila_actual = FILA_DATOS_INICIO + i - 1

            ultima_guardia, _ = calcular_guardias(medico)

            fila_datos = [
                i,
                valor_medico(medico, "cedula"),
                valor_medico(medico, "codigo"),
                valor_medico(medico, "nombres"),
                valor_medico(medico, "apellidos"),
                valor_medico(medico, "telefono"),
                valor_medico(medico, "correo"),
                formatear_fecha(valor_medico(medico, "fecha_ingreso", defecto=None)),
                valor_medico(medico, "cargo"),
                valor_medico(medico, "especialidad"),
                valor_medico(medico, "dependencia"),
                valor_medico(medico, "tipo_contratacion", "contratacion"),
                valor_medico(medico, "centro_salud", "centro"),
                valor_medico(medico, "asic"),
                valor_medico(medico, "tipologia_centro"),
                valor_medico(medico, "ubicacion_administrativa", "ubicacion"),
                valor_medico(medico, "estatus"),
                valor_medico(medico, "causa_inactividad"),
                formatear_fecha(medico.get("fecha_inicio_inactividad")),
                formatear_fecha(medico.get("fecha_fin_inactividad")),
                valor_medico(medico, "tiempo_inactividad", defecto="—"),
                valor_medico(medico, "formacion_estudiando", "formacion"),
                ultima_guardia,
            ]

            for col_idx, valor in enumerate(fila_datos, start=1):

                if col_idx in COLUMNAS_FECHA and valor not in (None, "—", ""):
                    valor = f"'{valor}"

                ws.Cells(fila_actual, col_idx).Value = valor

        # ------------------------------------------------------------
        # PIE DE TABLA (total de médicos)
        # ------------------------------------------------------------
        ws.Cells(fila_total, 1).Value = (
            f"Total de médicos exportados: {total_medicos}   |   "
            f"Generado el: {datetime.now().strftime('%d/%m/%Y')}"
        )

        # Guardar y cerrar
        wb.Save()
        wb.Close()

        if parent_window:
            mostrar_exito(parent_window, "Éxito", "El reporte Excel ha sido generado correctamente")

        if os.name == 'nt':
            os.startfile(ruta_guardado)

    except Exception as e:
        if parent_window:
            mostrar_error(parent_window, "Error inesperado", f"Ocurrió un error: {str(e)}")
    finally:
        if excel:
            excel.Quit()