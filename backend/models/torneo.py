class Torneo:
    """
    Un torneo.

    El estado es un dato del torneo y no algo que se calcule mirando sus
    partidos: un torneo puede estar planificado sin tener ningún partido
    todavía, y uno finalizado no debería reabrirse porque alguien edite
    un resultado viejo.
    """

    def __init__(self, id, nombre, modo, fecha, estado="planificado",
                 descripcion=None, lugar=None):
        self.id = id
        self.nombre = nombre
        self.modo = modo
        self.fecha = fecha
        self.estado = estado
        self.descripcion = descripcion
        self.lugar = lugar

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "modo": self.modo,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "estado": self.estado,
            "descripcion": self.descripcion,
            "lugar": self.lugar,
        }

    @staticmethod
    def from_row(row):
        return Torneo(
            id=row["id"],
            nombre=row["nombre"],
            modo=row["modo"],
            fecha=row["fecha"],
            estado=row["estado"],
            descripcion=row.get("descripcion"),
            lugar=row.get("lugar"),
        )
