class Jugador:
    """
    Un jugador del grupo.

    Los modelos son objetos planos: guardan datos y saben convertirse a
    diccionario, nada más. No consultan la base ni contienen reglas del
    negocio -- eso vive en los repositorios y los servicios. La ventaja es
    que se pueden crear en una prueba sin necesitar una base corriendo.
    """

    def __init__(self, id, nombre, fecha_nacimiento=None,
                 imagen_vertical_path=None, imagen_icono_path=None):
        self.id = id
        self.nombre = nombre
        self.fecha_nacimiento = fecha_nacimiento
        self.imagen_vertical_path = imagen_vertical_path
        self.imagen_icono_path = imagen_icono_path

    def to_dict(self):
        """Lo que viaja por la API. La fecha se serializa a texto porque
        un date de Python no es JSON válido."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "fecha_nacimiento": (
                self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None
            ),
            "imagen_vertical": self.imagen_vertical_path,
            "imagen_icono": self.imagen_icono_path,
        }

    @staticmethod
    def from_row(row):
        """Construye el modelo desde una fila de la base.

        Existe para que el mapeo entre columnas y atributos esté en UN
        lugar: si mañana se renombra una columna, se toca acá y no en cada
        consulta que devuelva jugadores."""
        return Jugador(
            id=row["id"],
            nombre=row["nombre"],
            fecha_nacimiento=row.get("fecha_nacimiento"),
            imagen_vertical_path=row.get("imagen_vertical_path"),
            imagen_icono_path=row.get("imagen_icono_path"),
        )
