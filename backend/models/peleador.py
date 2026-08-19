class Peleador:
    """
    Un personaje del juego.

    Mismo criterio que Jugador: objeto plano, sin consultas ni reglas.
    """

    def __init__(self, id, nombre, imagen_icono_path=None):
        self.id = id
        self.nombre = nombre
        self.imagen_icono_path = imagen_icono_path

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "imagen_icono": self.imagen_icono_path,
        }

    @staticmethod
    def from_row(row):
        return Peleador(
            id=row["id"],
            nombre=row["nombre"],
            imagen_icono_path=row.get("imagen_icono_path"),
        )
