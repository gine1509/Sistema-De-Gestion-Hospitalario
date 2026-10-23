from PIL import Image, ImageTk

ICONOS = {


# Sidebar
"inicio": "ui/Logos/hogar.png",
"medicos": "ui/Logos/asistencia-medica.png",
"guardias": "ui/Logos/calendario.png",
"oficios": "ui/Logos/oficios.png",
"configuracion": "ui/Logos/engranaje.png",
"direccion": "ui/Logos/secretario.png",
"salir": "ui/Logos/cerrar-sesion.png",

# Dashboard
"usuarios": "ui/Logos/asistencia-medica.png",
"especialidades": "ui/Logos/asistencia-medica.png",
"reportes": "ui/Logos/asistencia-medica.png",
"art8": "ui/Logos/asistencia-medica.png",
"inactivos": "ui/Logos/asistencia-medica.png",

 # Médicos
"hospital": "ui/Logos/hospital.png",
"telefono": "ui/Logos/llamar.png",
"ver": "ui/Logos/ver.png",
"informacion_personal": "ui/Logos/perfil-personal.png",
"informacion_profesional": "ui/Logos/maletin.png",
"horarios_y_guardias":"ui/Logos/guardias.png",


# Acciones
"agregar": "ui/Logos/agregar-usuario.png",
"editar": "ui/Logos/editarusuario.png",
"eliminar": "ui/Logos/eliminar-usuario.png",
"buscar": "ui/Logos/busqueda.png",
"filtro": "ui/Logos/filtro.png",
"exportar": "ui/Logos/bandeja-de-descarga.png",
"agregar_medico":"ui/Logos/agregar-usuario.png",
"agregar_oficio":"ui/Logos/agregar_oficio.png",
"cancelar": "ui/Logos/cerrar.png",
"guardar": "ui/Logos/marcador.png",
"guardar_pdf": "ui/Logos/guardar_pdf.png",
"guardar_excel": "ui/Logos/guardar_excel.png",
"fecha": "ui/Logos/fecha.png",
"calendario": "ui/Logos/fecha1.png",
"persona": "ui/Logos/persona.png",
"editar_oficio": "ui/Logos/editar-archivo.png",
"eliminar_oficio": "ui/Logos/eliminar-documento.png",
"agregar_personal":"ui/Logos/agregar-usuario.png",
"horario": "ui/Logos/horario1.png",
"usuario": "ui/Logos/usuario2.png",
"descarga_azul": "ui/Logos/descarga_azul.png",
"guardias_blanco": "ui/Logos/guardias_blanco.png",
"grupos": "ui/Logos/grupo.png",


#"exito": "",
#"error": "",
#"advertencia": "",
#"pregunta": "",


}

def cargar_icono(ruta, tamaño=24):


    try:

        imagen = Image.open(ruta)

        imagen = imagen.resize(
            (tamaño, tamaño),
            Image.Resampling.LANCZOS
        )

        return ImageTk.PhotoImage(imagen)

    except Exception as e:

        print(
            f"Error cargando icono: {ruta}\n{e}"
        )

        return None


def obtener_icono(nombre, tamaño=24):


        ruta = ICONOS.get(nombre)

        if not ruta:

            print(
                f"Icono '{nombre}' no encontrado"
            )

            return None

        return cargar_icono(
            ruta,
            tamaño
        )

