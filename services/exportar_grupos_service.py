import os
import calendar
from datetime import date, datetime
from collections import defaultdict
from tkinter import filedialog

import customtkinter as ctk
from xhtml2pdf import pisa

from ui.mensajes import mostrar_exito, mostrar_error
from services.exportar_medico_service import link_callback
from services.exportar_guardias_service import obtener_mes_texto
from services.guardia_service import (
    listar_grupos_articulo8,
    obtener_miembros_grupo_articulo8,
    obtener_horario_grupo_articulo8,
)
from ui.Modulos.Medicos.colores import COLOR_BLANCO, COLOR_TEXTO, COLOR_ROJO


# Igual que en guardias: semana empieza en domingo
_DIAS_SEMANA = ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"]


def _construir_semanas_unificado(anio, mes, dia_nombres):
    """
    dia_nombres = {date: [nombres...]}
    Construye las semanas del mes con todos los nombres que tienen guardia ese día.
    Semana empieza en domingo (igual que el reporte de guardias).
    """
    cal = calendar.Calendar(firstweekday=6)  # 6 = Domingo
    semanas = []
    for semana in cal.monthdayscalendar(anio, mes):
        fila = []
        for numero in semana:
            if numero == 0:
                fila.append(None)
                continue
            fecha = date(anio, mes, numero)
            nombres = dia_nombres.get(fecha, [])
            fila.append({
                "dia": numero,
                "tiene_guardia": bool(nombres),
                "nombres": nombres,
            })
        semanas.append(fila)
    return semanas


def exportar_horario_grupo_pdf(
    id_grupo,
    nombre_grupo,
    anio,
    mes,
    parent_window=None,
):
    miembros = obtener_miembros_grupo_articulo8(id_grupo)
    fechas = obtener_horario_grupo_articulo8(id_grupo)

    mes_texto = obtener_mes_texto(mes)
    nombre_archivo = f"Horario_Grupo_{nombre_grupo}_{mes_texto}_{anio}.pdf"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar horario del grupo (PDF)",
        initialfile=nombre_archivo,
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")],
    )
    if not filepath:
        return

    # Mapa simple para un solo grupo
    dia_nombres = defaultdict(list)
    nombres = [m.get("nombre", "").strip().upper() for m in (miembros or []) if m.get("nombre")]
    for f in (fechas or []):
        dia_nombres[f].extend(nombres)

    semanas = _construir_semanas_unificado(anio, mes, dia_nombres)

    encabezado_dias = "".join(
        f'<th style="width:14.28%;">{d}</th>' for d in _DIAS_SEMANA
    )

    filas_html = ""
    for semana in semanas:
        celdas = ""
        for celda in semana:
            if celda is None:
                celdas += '<td class="dia-vacio" style="width:14.28%;"></td>'
                continue
            if celda["tiene_guardia"]:
                nombres_html = "".join(
                    f'<div class="nombre-medico">{n}</div>'
                    for n in celda["nombres"]
                )
                celdas += (
                    f'<td class="dia-celda con-guardia" style="width:14.28%;">'
                    f'<div class="numero-dia">{celda["dia"]}</div>'
                    f'{nombres_html}'
                    f'</td>'
                )
            else:
                celdas += (
                    f'<td class="dia-celda" style="width:14.28%;">'
                    f'<div class="numero-dia">{celda["dia"]}</div>'
                    f'</td>'
                )
        filas_html += f"<tr>{celdas}</tr>"

    html_content = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: letter landscape;
                margin: 10mm 12mm 10mm 12mm;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 9pt;
                color: #1E293B;
            }}
            .header-logos {{ width: 100%; text-align: center; border: none; margin-bottom: 10px; }}
            .header-logos td {{ text-align: center; vertical-align: middle; }}
            .header-logo-normal {{ height: 42px; }}
            .header-logo-salud {{ height: 100px; }}
            .header-logo-hospital {{ height: 70px; }}
            .header-logo-barrio {{ height: 28px; }}
            .title-container {{ text-align: center; margin-bottom: 6px; }}
            .report-title {{ font-size: 14pt; font-weight: bold; margin: 2px 0; }}
            .subtitle {{ font-size: 11pt; font-weight: bold; color: #0F4C81; }}
            .separator {{ border-top: 2px solid #0F4C81; margin: 8px 0 12px 0; }}

            table.calendario {{
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                margin-bottom: 10px;
            }}
            table.calendario th {{
                background: #2563EB;
                color: #FFFFFF;
                border: 1px solid #1E3A8A;
                padding: 4px 0;
                text-align: center;
                font-size: 8.5pt;
                font-weight: bold;
            }}
            table.calendario td {{
                border: 1px solid #94A3B8;
                vertical-align: top;
                height: 58px;
                padding: 3px 2px;
                overflow: hidden;
            }}
            .dia-vacio {{ background: #F1F5F9; }}
            .dia-celda {{ background: #FFFFFF; }}
            .con-guardia {{ background: #DBEAFE; }}
            .numero-dia {{
                font-weight: bold;
                font-size: 10pt;
                color: #0F172A;
                margin-bottom: 1px;
            }}
            .nombre-medico {{
                font-size: 6.5pt !important;
                font-weight: bold;
                text-align: center;
                line-height: 1.1;
                margin: 0;
                padding: 0;
                color: #1E3A8A;
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: normal;
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
            <div class="report-title">HORARIO DE GUARDIAS — GRUPO MEDICO</div>
            <div class="subtitle">{nombre_grupo}  ·  {mes_texto} {anio}</div>
        </div>
        <div class="separator"></div>

        <table class="calendario">
            <tr>{encabezado_dias}</tr>
            {filas_html}
        </table>
    </body>
    </html>
    '''
    try:
        with open(filepath, "wb") as pdf_file:
            status = pisa.CreatePDF(html_content, dest=pdf_file, link_callback=link_callback)
        if status.err:
            mostrar_error(parent_window, "Error de exportación",
                          "Hubo un problema al generar el PDF del horario del grupo.")
        else:
            mostrar_exito(parent_window, "Exportación exitosa",
                          "El horario del grupo se generó correctamente en PDF.")
            if os.name == "nt":
                os.startfile(filepath)
    except Exception as e:
        mostrar_error(parent_window, "Error de exportación",
                      f"No se pudo generar el PDF:\n{e}")


def exportar_todos_los_grupos_pdf(anio, mes, parent_window=None):
    grupos = listar_grupos_articulo8()
    if not grupos:
        mostrar_error(parent_window, "Exportar", "No hay grupos registrados.")
        return

    mes_texto = obtener_mes_texto(mes)
    nombre_archivo = f"Horarios_Todos_Grupos_{mes_texto}_{anio}.pdf"

    filepath = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Guardar horarios de todos los grupos (PDF)",
        initialfile=nombre_archivo,
        defaultextension=".pdf",
        filetypes=[("Archivos PDF", "*.pdf")],
    )
    if not filepath:
        return

    # ---------- Un solo mapa de día → nombres de TODOS los grupos ----------
    dia_nombres = defaultdict(list)

    for grupo in grupos:
        miembros = obtener_miembros_grupo_articulo8(grupo["id_grupo"])
        fechas = obtener_horario_grupo_articulo8(grupo["id_grupo"]) or []
        nombres = [
            m.get("nombre", "").strip().upper()
            for m in (miembros or [])
            if m.get("nombre")
        ]
        for f in fechas:
            for n in nombres:
                if n not in dia_nombres[f]:
                    dia_nombres[f].append(n)

    semanas = _construir_semanas_unificado(anio, mes, dia_nombres)

    encabezado_dias = "".join(
        f'<th style="width:14.28%;">{d}</th>' for d in _DIAS_SEMANA
    )

    filas_html = ""
    for semana in semanas:
        celdas = ""
        for celda in semana:
            if celda is None:
                celdas += '<td class="dia-vacio" style="width:14.28%;"></td>'
                continue
            if celda["tiene_guardia"]:
                nombres_html = "".join(
                    f'<div class="nombre-medico">{n}</div>'
                    for n in celda["nombres"]
                )
                celdas += (
                    f'<td class="dia-celda con-guardia" style="width:14.28%;">'
                    f'<div class="numero-dia">{celda["dia"]}</div>'
                    f'{nombres_html}'
                    f'</td>'
                )
            else:
                celdas += (
                    f'<td class="dia-celda" style="width:14.28%;">'
                    f'<div class="numero-dia">{celda["dia"]}</div>'
                    f'</td>'
                )
        filas_html += f"<tr>{celdas}</tr>"

    html_content = f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: letter landscape;
                margin: 10mm 12mm 10mm 12mm;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 9pt;
                color: #1E293B;
            }}
            .header-logos {{ width: 100%; text-align: center; margin-bottom: 8px; }}
            .header-logos td {{ text-align: center; vertical-align: middle; }}
            .header-logo-normal {{ height: 42px; }}
            .header-logo-salud {{ height: 100px; }}
            .header-logo-hospital {{ height: 70px; }}
            .header-logo-barrio {{ height: 28px; }}
            .title-container {{ text-align: center; margin-bottom: 4px; }}
            .report-title {{ font-size: 14pt; font-weight: bold; }}
            .subtitle {{ font-size: 11pt; font-weight: bold; color: #0F4C81; }}
            .separator {{ border-top: 2px solid #0F4C81; margin: 6px 0 10px 0; }}

            table.calendario {{
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }}
            table.calendario th {{
                background: #2563EB;
                color: #FFFFFF;
                border: 1px solid #1E3A8A;
                padding: 4px 0;
                text-align: center;
                font-size: 8.5pt;
                font-weight: bold;
            }}
            table.calendario td {{
                border: 1px solid #94A3B8;
                vertical-align: top;
                height: 58px;
                padding: 3px 2px;
                overflow: hidden;
            }}
            .dia-vacio {{ background: #F1F5F9; }}
            .dia-celda {{ background: #FFFFFF; }}
            .con-guardia {{ background: #DBEAFE; }}
            .numero-dia {{
                font-weight: bold;
                font-size: 10pt;
                color: #0F172A;
                margin-bottom: 1px;
            }}
            .nombre-medico {{
                font-size: 6.5pt !important;
                font-weight: bold;
                text-align: center;
                line-height: 1.1;
                margin: 0;
                padding: 0;
                color: #1E3A8A;
                word-wrap: break-word;
                overflow-wrap: break-word;
                white-space: normal;
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
            <div class="report-title">HORARIOS DE GUARDIAS — TODOS LOS GRUPOS ARTÍCULO 8</div>
            <div class="subtitle">{mes_texto} {anio}</div>
        </div>
        <div class="separator"></div>

        <table class="calendario">
            <tr>{encabezado_dias}</tr>
            {filas_html}
        </table>
    </body>
    </html>
    '''
    try:
        with open(filepath, "wb") as pdf_file:
            status = pisa.CreatePDF(html_content, dest=pdf_file, link_callback=link_callback)
        if status.err:
            mostrar_error(parent_window, "Error de exportación",
                          "Hubo un problema al generar el PDF de todos los grupos.")
        else:
            mostrar_exito(parent_window, "Exportación exitosa",
                          "Los horarios de todos los grupos se generaron correctamente en un solo calendario.")
            if os.name == "nt":
                os.startfile(filepath)
    except Exception as e:
        mostrar_error(parent_window, "Error de exportación",
                      f"No se pudo generar el PDF:\n{e}")


def mostrar_dialogo_exportar_grupo(
    parent_window,
    id_grupo,
    nombre_grupo,
    mes,
    anio,
):
    """Diálogo bonito: exportar grupo actual o todos los grupos."""
    dialogo = ctk.CTkToplevel(parent_window)
    dialogo.title("Exportar horario")
    dialogo.geometry("420x260")
    dialogo.resizable(False, False)
    dialogo.configure(fg_color=COLOR_BLANCO)
    dialogo.transient(parent_window)
    dialogo.grab_set()

    dialogo.update_idletasks()
    x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - 210
    y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - 130
    dialogo.geometry(f"420x260+{x}+{y}")

    ctk.CTkLabel(
        dialogo,
        text="Exportar horario a PDF",
        font=("Segoe UI", 16, "bold"),
        text_color=COLOR_TEXTO,
    ).pack(pady=(22, 4))

    ctk.CTkLabel(
        dialogo,
        text=f"Grupo: {nombre_grupo}  ·  {obtener_mes_texto(mes)} {anio}",
        font=("Segoe UI", 10),
        text_color="#64748B",
    ).pack(pady=(0, 18))

    frame = ctk.CTkFrame(dialogo, fg_color=COLOR_BLANCO)
    frame.pack(fill="x", padx=30)

    def cerrar():
        if dialogo.winfo_exists():
            dialogo.destroy()

    def cmd_grupo():
        dialogo.withdraw()
        try:
            exportar_horario_grupo_pdf(
                id_grupo=id_grupo,
                nombre_grupo=nombre_grupo,
                anio=anio,
                mes=mes,
                parent_window=parent_window,
            )
        finally:
            cerrar()

    def cmd_todos():
        dialogo.withdraw()
        try:
            exportar_todos_los_grupos_pdf(
                anio=anio,
                mes=mes,
                parent_window=parent_window,
            )
        finally:
            cerrar()

    ctk.CTkButton(
        frame,
        text="Solo este grupo",
        font=("Segoe UI", 13, "bold"),
        text_color="white",
        fg_color=COLOR_ROJO,
        hover_color="#B91C1C",
        corner_radius=10,
        height=48,
        command=cmd_grupo,
    ).pack(fill="x", pady=(0, 10))

    ctk.CTkButton(
        frame,
        text="Todos los grupos",
        font=("Segoe UI", 13, "bold"),
        text_color="white",
        fg_color="#0F4C81",
        hover_color="#0A3A63",
        corner_radius=10,
        height=48,
        command=cmd_todos,
    ).pack(fill="x")