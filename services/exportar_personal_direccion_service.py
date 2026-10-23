import os
import calendar
from datetime import date, datetime, timedelta
from tkinter import filedialog

import customtkinter as ctk
from xhtml2pdf import pisa

from ui.mensajes import mostrar_exito, mostrar_error
from services.exportar_medico_service import link_callback, obtener_ruta_base
from services.personal_direccion_service import listar_personal_direccion, DIAS_SEMANA
from ui.iconos import obtener_icono

COLOR_BLANCO = "#FFFFFF"
COLOR_TEXTO = "#0F172A"
COLOR_AZUL = "#2563EB"
COLOR_AZUL_OSCURO = "#0F4C81"
COLOR_ROJO = "#DC2626"
COLOR_GRIS = "#475569"

FIRMA_DIRECTOR_NOMBRE = "CNEL. YONY ALBINO CARRILLO GARCÍA"
FIRMA_DIRECTOR_CARGO = "DIRECTOR DEL HOSPITAL PBRO. JUSTO PASTOR ARIAS DE RUBIO"
FIRMA_PROVIDENCIA = "PROVIDENCIA ADMINISTRATIVA N° 3792-2025 DE FECHA 05/05/2025 CORPORACION DE SALUD DEL ESTADO TACHIRA"

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
DIAS_CORTOS = ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"]


def _fecha(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(valor.strip(), formato).date()
            except ValueError:
                pass
    return None


def _nombre_mes(mes):
    return MESES[mes - 1]


def _formatear_fecha(fecha):
    return f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year}"


def _causa(persona):
    return (persona.get("causa_inactividad") or "Reposo médico").strip()


def _es_definitiva(causa):
    texto = (causa or "").lower()
    return any(palabra in texto for palabra in ("renuncia", "renunció", "jubil", "retiro", "retiró"))


def _esta_inactivo_en_fecha(persona, fecha):
    if persona.get("activo", True):
        return False

    inicio = _fecha(persona.get("fecha_inicio_inactividad"))
    fin = _fecha(persona.get("fecha_fin_inactividad"))

    if inicio and fin:
        return inicio <= fecha <= fin
    if inicio and not fin:
        return fecha >= inicio
    if fin and not inicio:
        return fecha <= fin
    return True


def _inactividad_solapa_mes(persona, inicio_mes, fin_mes):
    if persona.get("activo", True):
        return False

    inicio = _fecha(persona.get("fecha_inicio_inactividad"))
    fin = _fecha(persona.get("fecha_fin_inactividad"))

    if _es_definitiva(_causa(persona)):
        return bool(inicio and inicio_mes <= inicio <= fin_mes)

    if inicio and fin:
        return inicio <= fin_mes and fin >= inicio_mes
    if inicio:
        return inicio <= fin_mes
    if fin:
        return fin >= inicio_mes
    return True


def _esta_asignado(persona, fecha):
    return fecha.isoweekday() in {h.get("dia") for h in persona.get("horarios", [])}


def _observaciones_mes(personas, anio, mes):
    inicio_mes = date(anio, mes, 1)
    fin_mes = date(anio, mes, calendar.monthrange(anio, mes)[1])
    observaciones = []

    for persona in personas:
        if not _inactividad_solapa_mes(persona, inicio_mes, fin_mes):
            continue

        nombre = (persona.get("nombre") or "SIN NOMBRE").upper()
        causa = _causa(persona)
        inicio = _fecha(persona.get("fecha_inicio_inactividad"))
        fin = _fecha(persona.get("fecha_fin_inactividad"))

        if _es_definitiva(causa):
            if inicio:
                observaciones.append(f"{nombre} — {causa.upper()} desde el {_formatear_fecha(inicio)}.")
            else:
                observaciones.append(f"{nombre} — {causa.upper()}.")
            continue

        if inicio and fin:
            if inicio == fin:
                rango = f"el {_formatear_fecha(inicio)}"
            else:
                rango = f"del {_formatear_fecha(inicio)} al {_formatear_fecha(fin)}"
        elif inicio:
            rango = f"desde el {_formatear_fecha(inicio)}"
        elif fin:
            rango = f"hasta el {_formatear_fecha(fin)}"
        else:
            rango = "por tiempo indefinido"

        observaciones.append(f"{nombre} — {causa.upper()}, {rango}.")

    return observaciones


def _observaciones_semana(personas, lunes, viernes):
    """Solo salidas definitivas, durante la semana en que ocurren."""
    observaciones = []
    for persona in personas:
        if persona.get("activo", True):
            continue
        causa = _causa(persona)
        if not _es_definitiva(causa):
            continue
        inicio = _fecha(persona.get("fecha_inicio_inactividad"))
        if inicio and lunes <= inicio <= viernes:
            nombre = (persona.get("nombre") or "SIN NOMBRE").upper()
            observaciones.append(f"{nombre} — {causa.upper()} desde el {_formatear_fecha(inicio)}.")
    return observaciones


def _logo_paths():
    base = obtener_ruta_base()
    return [
        os.path.join(base, "ui", "Logos", "Logo-Min-Salud-2009.png"),
        os.path.join(base, "ui", "Logos", "logo.png"),
        os.path.join(base, "ui", "Logos", "Barrio-adentro.png"),
        os.path.join(base, "ui", "Logos", "spns.png"),
        os.path.join(base, "ui", "Logos", "cropped-Logo-Nuevo-Fondo-Blanco-1.png"),
    ]


def _logos_html():
    rutas = _logo_paths()
    clases = ["logo-salud", "logo-hospital", "logo-barrio", "logo-normal", "logo-normal"]
    partes = []
    for ruta, clase in zip(rutas, clases):
        partes.append(f'<td><img src="{ruta}" class="{clase}"></td>')
    return "".join(partes)


def _firma_html():
    return f'''
    <table class="firmas">
        <tr><td>
            <div class="linea-firma">________________________________________</div>
            <div class="firma-nombre">{FIRMA_DIRECTOR_NOMBRE}</div>
            <div class="firma-cargo">{FIRMA_DIRECTOR_CARGO}</div>
            <div class="firma-prov">{FIRMA_PROVIDENCIA}</div>
        </td></tr>
    </table>
    '''


def exportar_horario_personal_pdf(anio, mes, texto_busqueda="", parent_window=None):
    personas = listar_personal_direccion(texto_busqueda)
    nombre_archivo = f"Rol_Guardias_Direccion_{_nombre_mes(mes)}_{anio}.pdf"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar rol de guardias del personal administrativo de dirección",
        initialfile=nombre_archivo,
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")]
    )
    if not filepath:
        return

    cal = calendar.Calendar(firstweekday=6)
    semanas = cal.monthdayscalendar(anio, mes)
    filas = []

    for semana in semanas:
        celdas = []
        for numero_dia in semana:
            if not numero_dia:
                celdas.append('<td class="vacio"></td>')
                continue

            fecha_dia = date(anio, mes, numero_dia)
            nombres = []
            for persona in personas:
                if not _esta_asignado(persona, fecha_dia):
                    continue
                # El rol mensual respeta el comportamiento del calendario del módulo:
                # las inactividades que afectan ese día no aparecen en la celda.
                if _esta_inactivo_en_fecha(persona, fecha_dia):
                    continue
                nombres.append((persona.get("nombre") or "SIN NOMBRE").upper())

            if nombres:
                contenido = "".join(
                    f'<div class="persona" style="font-size:6.5pt !important; line-height:1.1;">{nombre}</div>'
                    for nombre in nombres
                )
            else:
                contenido = '<div class="sin-personal">—</div>'

            celdas.append(
                f'<td><div class="numero">{numero_dia}</div>{contenido}</td>'
            )
        filas.append("<tr>" + "".join(celdas) + "</tr>")

    observaciones = _observaciones_mes(personas, anio, mes)
    obs_html = "".join(f'<div class="obs">• {texto}</div>' for texto in observaciones)
    if not obs_html:
        obs_html = '<div class="obs">No se registran observaciones para este período.</div>'
    cols_html = "".join('<col style="width: 14.28%;">' for _ in range(7))
    html = f'''<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><style>

@page {{
    size: letter landscape;
    margin: 8mm 12mm 9mm 12mm;
}}

body {{
    font-family: Arial, sans-serif;
    font-size: 8pt;
    color: #000;
}}

.logos {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 5mm;
}}

.logos td {{
    text-align: center;
    vertical-align: middle;
    border: none;
}}

.logo-normal {{
    height: 42px;
}}

.logo-salud {{
    height: 105px;
}}

.logo-hospital {{
    height: 68px;
}}

.logo-barrio {{
    height: 30px;
}}

.titulo {{
    text-align: center;
    font-size: 14pt;
    font-weight: bold;
    margin: 0;
}}

.subtitulo {{
    text-align: center;
    color: {COLOR_AZUL_OSCURO};
    font-size: 10.5pt;
    font-weight: bold;
    margin-top: 2px;
}}

.linea {{
    border-top: 2px solid {COLOR_AZUL_OSCURO};
    margin: 4px 0 7px 0;
}}

/* ============================================================
   CALENDARIO
   ============================================================ */

.calendario {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}}

.calendario th {{
    background: #2563EB;
    color: white;
    border: 1px solid #1E3A8A;
    height: 20px;
    font-size: 8pt;
    font-weight: bold;
    width: 14.28%;
    text-align: center;
    vertical-align: middle;
    padding: 2px;
}}

.calendario td {{
    border: 1px solid #94A3B8;
    vertical-align: top;
    height: 90px;          /* antes 70px */
    padding: 2px 3px;
    width: 14.28%;
}}

.calendario .vacio {{
    background: #F1F5F9;
}}

/* Número del día */
.numero {{
    font-weight: bold;
    font-size: 8pt;
    line-height: 1;
    margin-bottom: 1px;
    text-align: left;
}}

/* ============================================================
   NOMBRES
   Todos los nombres tienen EXACTAMENTE el mismo tamaño
   ============================================================ */

.persona {{
    font-family: Arial, sans-serif;
    font-size: 5.5pt !important;
    font-weight: bold;
    text-align: center;
    line-height: 1.1;
    margin: 0.5px 0;
    
}}

/* Cuando hay varios nombres, todos mantienen el mismo tamaño */
.persona + .persona {{
    margin-top: 2px;
}}

.sin-personal {{
    text-align: center;
    color: #64748B;
    font-size: 8pt;
    margin-top: 10px;
}}

/* ============================================================
   OBSERVACIONES
   ============================================================ */

.seccion {{
    font-size: 8pt;
    font-weight: bold;
    color: {COLOR_AZUL_OSCURO};
    margin: 6px 0 3px 0;
}}

.obs {{
    font-family: Arial, sans-serif;
    font-size: 8pt;
    font-weight: normal;
    line-height: 1.1;
    margin: 2px 0;
    word-wrap: break-word;
}}

/* ============================================================
   FIRMA DEL DIRECTOR
   Todo el bloque mantiene tamaños uniformes
   ============================================================ */

.firmas {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 25px;
    page-break-inside: avoid;
}}

.firmas td {{
    text-align: center;
    border: none;
    vertical-align: top;
}}

.linea-firma {{
    font-family: Arial, sans-serif;
    font-size: 8pt;
    line-height: 1;
    margin-bottom: 2px;
}}

.firma-nombre {{
    font-family: Arial, sans-serif;
    font-size: 8pt;
    font-weight: bold;
    line-height: 1.1;
    margin-top: 0;
}}

.firma-cargo {{
    font-family: Arial, sans-serif;
    font-size: 8pt;
    font-weight: bold;
    line-height: 1.1;
    margin-top: 2px;
}}

.firma-prov {{
    font-family: Arial, sans-serif;
    font-size: 8pt;
    font-weight: bold;
    line-height: 1.1;
    margin-top: 2px;
}}

</style></head><body>

<table class="logos"><tr>{_logos_html()}</tr></table>

<div class="titulo">
    ROL DE GUARDIAS DEL PERSONAL ADMINISTRATIVO DE DIRECCIÓN
</div>

<div class="subtitulo">
    {_nombre_mes(mes).upper()} {anio}
</div>

<div class="linea"></div>

<table class="calendario">
    <colgroup>{cols_html}</colgroup>

    <tr>
        {''.join(f'<th>{d}</th>' for d in DIAS_CORTOS)}
    </tr>

    {''.join(filas)}

</table>

<div class="seccion">OBSERVACIONES</div>

{obs_html}

{_firma_html()}

</body></html>'''

    try:
        with open(filepath, "wb") as archivo:
            estado = pisa.CreatePDF(html, dest=archivo, link_callback=link_callback)
        if estado.err:
            mostrar_error(parent_window, "Error de exportación", "Hubo un problema al generar el PDF del horario de dirección.")
        else:
            mostrar_exito(parent_window, "Exportación exitosa", "El rol mensual de dirección se generó correctamente en PDF.")
            if os.name == "nt":
                os.startfile(filepath)
    except Exception as e:
        mostrar_error(parent_window, "Error de exportación", f"No se pudo generar el PDF:\n{e}")


def _rango_semana_actual():
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    viernes = lunes + timedelta(days=4)
    return lunes, viernes

def _rango_semana_desde_fecha(fecha):
    """Devuelve (lunes, viernes) de la semana laboral que contiene `fecha`."""
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    if not isinstance(fecha, date):
        return _rango_semana_actual()
    lunes = fecha - timedelta(days=fecha.weekday())
    viernes = lunes + timedelta(days=4)
    return lunes, viernes


def _filas_asistencia(personas, lunes):
    filas = []
    for offset in range(5):
        fecha_dia = lunes + timedelta(days=offset)
        asignados = []
        for persona in personas:
            if not _esta_asignado(persona, fecha_dia):
                continue
            nombre = (persona.get("nombre") or "SIN NOMBRE").upper()
            inactivo = _esta_inactivo_en_fecha(persona, fecha_dia)
            causa = _causa(persona) if inactivo else ""
            if inactivo and _es_definitiva(causa):
                continue
            asignados.append({
                "nombre": nombre,
                "cedula": persona.get("cedula") or "",
                "cargo": persona.get("cargo") or "",
                "causa": causa,
            })
        filas.append((fecha_dia, asignados))
    return filas


def exportar_asistencia_personal_pdf(lunes, viernes, texto_busqueda="", parent_window=None):
    personas = listar_personal_direccion(texto_busqueda)
    if not personas:
        mostrar_error(parent_window, "Sin registros", "No hay personal de dirección registrado.")
        return

    nombre_archivo = f"Control_Asistencia_Direccion_{lunes.strftime('%d-%m-%Y')}.pdf"
    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar control de asistencias de dirección",
        initialfile=nombre_archivo,
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")]
    )
    if not filepath:
        return

    filas = _filas_asistencia(personas, lunes)
    cuerpo = []
    nombres_dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]

    for (fecha_dia, asignados), nombre_dia in zip(filas, nombres_dias):
        fecha_str = f"<b>{nombre_dia}</b><br>{fecha_dia.strftime('%d/%m/%Y')}"
        
        if not asignados:
            cuerpo.append(f'''
            <tr>
                <td class="fecha">{fecha_str}</td>
                <td></td><td></td><td></td><td></td><td></td><td></td><td></td>
            </tr>''')
        else:
            rowspan = len(asignados)
            for i, persona in enumerate(asignados):
                nombre = persona["nombre"]
                causa = persona["causa"]
                cedula = persona["cedula"]
                cargo = persona["cargo"]
                
                nombre_celda = f'<span class="texto-tabla">{nombre}</span>'
                
                # Si el trabajador tiene causa/inactividad (reposo, vacaciones, etc.)
                if causa:
                    # Se combinan las 4 columnas (Hora entrada, Salida, Firma, Observación)
                    celdas_derecha = f'<td class="dato causa" colspan="4">{causa.upper()}</td>'
                else:
                    # Celdas normales en blanco para llenado manual
                    celdas_derecha = '<td></td><td></td><td></td><td></td>'

                if i == 0:
                    cuerpo.append(f'''
                    <tr>
                        <td class="fecha" rowspan="{rowspan}">{fecha_str}</td>
                        <td class="dato">{nombre_celda}</td>
                        <td class="dato">{cedula}</td>
                        <td class="dato">{cargo}</td>
                        {celdas_derecha}
                    </tr>''')
                else:
                    cuerpo.append(f'''
                    <tr>
                        <td class="dato">{nombre_celda}</td>
                        <td class="dato">{cedula}</td>
                        <td class="dato">{cargo}</td>
                        {celdas_derecha}
                    </tr>''')

    observaciones = _observaciones_semana(personas, lunes, viernes)
    obs_html = "".join(f'<div class="obs">• {texto}</div>' for texto in observaciones)
    if not obs_html:
        obs_html = '<div class="obs">No se registran observaciones para esta semana.</div>'

    html = f'''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><style>

        @page {{
            size: letter landscape;
            margin: 8mm 12mm 9mm 12mm;
        }}

        body {{
            font-family: Arial, sans-serif;
            color:#000;
            font-size:8pt;
        }}

        .logos {{
            width:100%;
            border-collapse:collapse;
            margin-bottom:2mm;
        }}

        .logos td {{
            text-align:center;
            vertical-align:middle;
            border:none;
        }}

        .logo-normal {{ height:36px; }}
        .logo-salud {{ height:82px; }}
        .logo-hospital {{ height:55px; }}
        .logo-barrio {{ height:25px; }}

        .titulo {{
            text-align:center;
            font-size:13pt;
            font-weight:bold;
            margin-top:1mm;
        }}

        .subtitulo {{
            text-align:center;
            font-size:9pt;
            font-weight:bold;
            margin-top:2px;
        }}

        .linea {{
            border-top:2px solid {COLOR_AZUL_OSCURO};
            margin:4px 0 7px 0;
        }}

        /* ============================================================
        TABLA DE ASISTENCIA
        ============================================================ */

        .asistencia {{
            width:100%;
            border-collapse:collapse;
            table-layout:fixed;
            font-size:8pt;
        }}

        .asistencia th {{
            border:1px solid #7B8794;
            background:#E5E7EB;
            color:#111827;
            font-size:8pt;
            font-weight:bold;
            padding:0px 0px;
            text-align:center;
            vertical-align:middle;
            line-height:1.1;
        }}

        .asistencia td {{
            border:1px solid #9CA3AF;
            height:28px;
            vertical-align:middle;
            padding:0px 0px;
            font-size:8pt;
            line-height:1.1;
            text-align:center;
        }}

        .asistencia .fecha {{
            text-align:center;
            background:#F8FAFC;
            font-size:8pt;
            font-weight:normal;
        }}

        .dato {{
            text-align:center;
            font-size:8pt;
            line-height:1.1;
            word-wrap:break-word;
        }}

        .texto-tabla {{
            font-size:8pt;
        }}

        .causa {{
            font-size:8pt;
            font-weight:bold;
            color:#000000;
        }}

        /* ============================================================
        OBSERVACIONES Y FIRMA
        ============================================================ */

        .seccion {{
            font-size:9pt;
            font-weight:bold;
            color:{COLOR_AZUL_OSCURO};
            margin:7px 0 3px 0;
        }}

        .obs {{
            font-size:8pt;
            line-height:1.1;
            margin:2px 0;
        }}

        .firmas {{
            width:100%;
            border-collapse:collapse;
            margin-top:40px;
            page-break-inside:avoid;
        }}

        .firmas td {{
            text-align:center;
            border:none;
        }}

        .linea-firma {{
            font-size:8pt;
            margin-bottom:-5px;
        }}

        .firma-nombre {{
            font-size:8pt;
            font-weight:bold;
            margin-top: 0px;
        }}

        .firma-cargo {{
            font-size:7.5pt;
            margin-top: 1px;
        }}

        .firma-prov {{
            font-size:6.5pt;
            margin-top:1px;
        }}

        </style></head><body>

        <table class="logos">
            <tr>{_logos_html()}</tr>
        </table>

        <div class="titulo">
            CONTROL DE ASISTENCIAS DIRECCION
        </div>

        <div class="subtitulo">
            SEMANA DESDE EL LUNES {lunes.strftime('%d/%m/%Y')}
            HASTA EL VIERNES {viernes.strftime('%d/%m/%Y')}
        </div>

        <div class="linea"></div>

        <table class="asistencia">

            <colgroup>
                <col style="width:10%;">
                <col style="width:22%;">
                <col style="width:12%;">
                <col style="width:16%;">
                <col style="width:8%;">
                <col style="width:8%;">
                <col style="width:10%;">
                <col style="width:15%;">
            </colgroup>

            <tr>
                <th>FECHA</th>
                <th>NOMBRES Y APELLIDOS</th>
                <th>CÉDULA</th>
                <th>CARGO</th>
                <th>HORA DE<br>ENTRADA</th>
                <th>HORA DE<br>SALIDA</th>
                <th>FIRMA</th>
                <th>OBSERVACIÓN</th>
            </tr>

            {''.join(cuerpo)}

        </table>

        {_firma_html()}

        </body></html>'''

    try:
        with open(filepath, "wb") as archivo:
            estado = pisa.CreatePDF(html, dest=archivo, link_callback=link_callback)
        if estado.err:
            mostrar_error(parent_window, "Error de exportación", "Hubo un problema al generar la planilla de asistencia.")
        else:
            mostrar_exito(parent_window, "Exportación exitosa", "El control semanal de asistencias se generó correctamente en PDF.")
            if os.name == "nt":
                os.startfile(filepath)
    except Exception as e:
        mostrar_error(parent_window, "Error de exportación", f"No se pudo generar el PDF:\n{e}")


def mostrar_dialogo_exportar_asistencia(parent_window=None, texto_busqueda=""):
    lunes, viernes = _rango_semana_actual()
    estado = {"lunes": lunes, "viernes": viernes}

    dialogo = ctk.CTkToplevel(parent_window)
    dialogo.title("Exportar asistencia")

    ancho, alto = 420, 280
    dialogo.geometry(f"{ancho}x{alto}")
    dialogo.resizable(False, False)
    dialogo.configure(fg_color=COLOR_BLANCO)

    if parent_window:
        dialogo.transient(parent_window)
    dialogo.grab_set()

    dialogo.update_idletasks()
    pos_x = (dialogo.winfo_screenwidth() // 2) - (ancho // 2)
    pos_y = (dialogo.winfo_screenheight() // 2) - (alto // 2)
    dialogo.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")

    ctk.CTkLabel(
        dialogo,
        text="Exportar asistencia semanal",
        font=("Segoe UI", 17, "bold"),
        text_color=COLOR_TEXTO,
        fg_color=COLOR_BLANCO,
    ).pack(pady=(22, 8))

    label_rango = ctk.CTkLabel(
        dialogo,
        text="",
        font=("Segoe UI", 12, "bold"),
        text_color="#000000",
        fg_color=COLOR_BLANCO,
        justify="center",
    )
    label_rango.pack(pady=(0, 14))

    def actualizar_rango(fecha_ref):
        l, v = _rango_semana_desde_fecha(fecha_ref)
        estado["lunes"], estado["viernes"] = l, v
        label_rango.configure(
            text=(
                f"SEMANA DESDE EL LUNES\n"
                f"{l.strftime('%d/%m/%Y')}\n"
                f"HASTA EL VIERNES\n"
                f"{v.strftime('%d/%m/%Y')}"
            )
        )

    def semana_anterior():
        actualizar_rango(estado["lunes"] - timedelta(days=7))

    def semana_siguiente():
        actualizar_rango(estado["lunes"] + timedelta(days=7))

    def ir_semana_actual():
        actualizar_rango(date.today())

    fila_nav = ctk.CTkFrame(dialogo, fg_color="transparent")
    fila_nav.pack(pady=(0, 16))

    ctk.CTkButton(
        fila_nav,
        text="‹ Anterior",
        width=100,
        height=32,
        fg_color="#64748B",
        hover_color="#475569",
        font=("Segoe UI", 12, "bold"),
        command=semana_anterior,
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        fila_nav,
        text="Esta semana",
        width=110,
        height=32,
        fg_color=COLOR_AZUL,
        hover_color=COLOR_AZUL_OSCURO,
        font=("Segoe UI", 12, "bold"),
        command=ir_semana_actual,
    ).pack(side="left", padx=4)

    ctk.CTkButton(
        fila_nav,
        text="Siguiente ›",
        width=100,
        height=32,
        fg_color="#64748B",
        hover_color="#475569",
        font=("Segoe UI", 12, "bold"),
        command=semana_siguiente,
    ).pack(side="left", padx=4)

    actualizar_rango(estado["lunes"])

    def exportar():
        dialogo.withdraw()
        try:
            exportar_asistencia_personal_pdf(
                estado["lunes"],
                estado["viernes"],
                texto_busqueda=texto_busqueda,
                parent_window=parent_window,
            )
        finally:
            if dialogo.winfo_exists():
                dialogo.destroy()

    icono_pdf = obtener_icono("guardar_pdf", 24)

    ctk.CTkButton(
        dialogo,
        text="Exportar PDF",
        image=icono_pdf,
        compound="left",
        width=170,
        height=50,
        fg_color=COLOR_ROJO,
        hover_color="#B91C1C",
        font=("Segoe UI", 12, "bold"),
        command=exportar,
    ).pack(pady=6)

    return dialogo


# Compatibilidad: los nombres anteriores dejan de exportar Excel y ahora generan PDF.
def exportar_horario_personal_excel(parent_window=None, texto_busqueda=""):
    hoy = date.today()
    exportar_horario_personal_pdf(hoy.year, hoy.month, texto_busqueda, parent_window)


def exportar_asistencia_personal_excel(parent_window=None, texto_busqueda=""):
    lunes, viernes = _rango_semana_actual()
    exportar_asistencia_personal_pdf(lunes, viernes, texto_busqueda, parent_window)
