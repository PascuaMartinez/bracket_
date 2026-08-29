class Partido:
    """Un enfrentamiento entre dos jugadores."""

    def __init__(self, id, torneo_id, jugador1_id, jugador2_id, ganador_id=None,
                 jugador1_peleador_id=None, jugador2_peleador_id=None,
                 rondas_jugadas=None, orden=None, jornada=None, ronda=None,
                 es_pase_libre=False, es_desempate=False,
                 es_tercer_puesto=False,
                 estado="pendiente", fecha_jugado=None):
        self.id = id
        self.torneo_id = torneo_id
        self.jugador1_id = jugador1_id
        self.jugador2_id = jugador2_id
        self.ganador_id = ganador_id
        self.jugador1_peleador_id = jugador1_peleador_id
        self.jugador2_peleador_id = jugador2_peleador_id
        self.rondas_jugadas = rondas_jugadas
        self.orden = orden
        self.jornada = jornada
        self.ronda = ronda
        self.es_pase_libre = es_pase_libre
        self.es_desempate = es_desempate
        self.es_tercer_puesto = es_tercer_puesto
        self.estado = estado
        self.fecha_jugado = fecha_jugado

    def to_dict(self):
        return {
            "id": self.id,
            "torneo_id": self.torneo_id,
            "jugador1_id": self.jugador1_id,
            "jugador2_id": self.jugador2_id,
            "ganador_id": self.ganador_id,
            "jugador1_peleador_id": self.jugador1_peleador_id,
            "jugador2_peleador_id": self.jugador2_peleador_id,
            "rondas_jugadas": self.rondas_jugadas,
            "orden": self.orden,
            "jornada": self.jornada,
            "ronda": self.ronda,
            "es_pase_libre": self.es_pase_libre,
            "es_desempate": self.es_desempate,
            "es_tercer_puesto": self.es_tercer_puesto,
            "estado": self.estado,
            "fecha_jugado": self.fecha_jugado.isoformat() if self.fecha_jugado else None,
        }

    @staticmethod
    def from_row(row):
        return Partido(
            id=row["id"],
            torneo_id=row["torneo_id"],
            jugador1_id=row["jugador1_id"],
            jugador2_id=row["jugador2_id"],
            ganador_id=row.get("ganador_id"),
            jugador1_peleador_id=row.get("jugador1_peleador_id"),
            jugador2_peleador_id=row.get("jugador2_peleador_id"),
            rondas_jugadas=row.get("rondas_jugadas"),
            orden=row.get("orden"),
            jornada=row.get("jornada"),
            ronda=row.get("ronda"),
            es_pase_libre=bool(row.get("es_pase_libre", False)),
            es_desempate=bool(row.get("es_desempate", False)),
            es_tercer_puesto=bool(row.get("es_tercer_puesto", False)),
            estado=row.get("estado", "pendiente"),
            fecha_jugado=row.get("fecha_jugado"),
        )
