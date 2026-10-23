import tkinter as tk

from PIL import Image, ImageTk

from ui.iconos import obtener_icono


def cargar_icono(ruta, tamaño=24):
    imagen = Image.open(ruta)
    imagen = imagen.resize((tamaño, tamaño), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(imagen)


class Sidebar(tk.Frame):

    def __init__(
        self,
        parent,
        mostrar_inicio,
        mostrar_medicos,
        mostrar_guardias,
        mostrar_oficios,
        mostrar_direccion,
        mostrar_configuracion,
        cerrar_sesion,
        salir
    ):
        super().__init__(parent, bg="#082B57", width=210)
        self.pack_propagate(False)

        # =====================
        # LOGO SUPERIOR
        # =====================
        logo_frame = tk.Frame(self, bg="#082B57")
        logo_frame.pack(fill="x", pady=(10, 5))

        try:
            self.logo_img = tk.PhotoImage(file="ui/Logos/logo_blanco.png")
            self.logo_img = self.logo_img.subsample(4, 4)

            tk.Label(
                logo_frame,
                image=self.logo_img,
                bg="#082B57"
            ).pack()

            tk.Label(
                logo_frame,
                text="Departamento de Dirección",
                bg="#082B57",
                fg="#B8C7E0",
                font=("Segoe UI", 10, "bold")
            ).pack(pady=(0, 0))
        except:
            pass

        tk.Frame(
            self,
            bg="#154A86",
            height=1
        ).pack(fill="x", padx=15, pady=10)

        # =====================
        # ICONOS
        # =====================
        self.icon_inicio = obtener_icono("inicio", 22)
        self.icon_medicos = obtener_icono("medicos", 22)
        self.icon_guardias = obtener_icono("guardias", 22)
        self.icon_oficios = obtener_icono("oficios", 22)
        self.icon_direccion = obtener_icono("direccion", 22)
        self.icon_config = obtener_icono("configuracion", 22)
        self.icon_salir = obtener_icono("salir", 22)

        # =====================
        # MENÚ SUPERIOR
        # =====================
        menu_superior = tk.Frame(self, bg="#082B57")
        menu_superior.pack(fill="x", anchor="n")

        self.crear_boton(
            menu_superior, "Inicio",
            self.icon_inicio, mostrar_inicio
        )

        self.crear_boton(
            menu_superior, "Médicos",
            self.icon_medicos, mostrar_medicos
        )

        self.crear_boton(
            menu_superior, "Guardias",
            self.icon_guardias, mostrar_guardias
        )

        self.crear_boton(
            menu_superior, "Oficios",
            self.icon_oficios, mostrar_oficios
        )

        # NUEVO: DIRECCIÓN
        self.crear_boton(
            menu_superior, "Dirección",
            self.icon_direccion, mostrar_direccion
        )

        # =====================
        # ESPACIO FLEXIBLE
        # =====================
        espacio = tk.Frame(self, bg="#082B57")
        espacio.pack(expand=True, fill="both")

        # =====================
        # CONFIGURACIÓN + SALIR
        # =====================
        menu_inferior = tk.Frame(self, bg="#082B57")
        menu_inferior.pack(
            fill="x",
            side="bottom",
            pady=(0, 15)
        )

        self.crear_boton(
            menu_inferior,
            "Configuración",
            self.icon_config,
            mostrar_configuracion
        )

        # NUEVO: CERRAR SESIÓN
        self.crear_boton(
            menu_inferior,
            "Cerrar sesión",
            self.icon_salir,
            cerrar_sesion
        )

       

    def crear_boton(
        self,
        parent,
        texto,
        icono,
        comando=None
    ):
        btn = tk.Button(
            parent,
            text=texto,
            image=icono,
            compound="left",
            command=comando,
            bg="#082B57",
            fg="white",
            activebackground="#0B4F94",
            activeforeground="white",
            relief="flat",
            borderwidth=0,
            anchor="w",
            cursor="hand2",
            padx=12,
            pady=12,
            font=("Segoe UI", 12, "bold")
        )

        btn.pack(
            fill="x",
            padx=10,
            pady=3
        )

        btn.bind(
            "<Enter>",
            lambda e: btn.config(bg="#0B4F94")
        )

        btn.bind(
            "<Leave>",
            lambda e: btn.config(bg="#082B57")
        )

        # Conserva la referencia del icono para evitar que Tkinter
        # lo elimine por garbage collection.
        btn._icon_ref = icono

        return btn
