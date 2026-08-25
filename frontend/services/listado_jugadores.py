"""
El listado de jugadores, con sus datos y ordenado.

Los datos para ordenar -- win rate, rating, partidos -- salen de la tabla
histórica, que ya los calcula para todos y está cacheada. Pedirlos jugador
por jugador serían tantas consultas como jugadores haya, para mostrar una
lista.
"""
from services import api

# Cómo se puede ordenar. La clave es lo que viaja en la dirección, y la
# función dice de dónde sacar el valor.
ORDENES = {
    "nombre": {"etiqueta": "Nombre", "valor": lambda j: (j["nombre"] or "").lower()},
    "rating": {"etiqueta": "Rating", "valor": lambda j: j["rating"]},
    "win_rate": {"etiqueta": "Win rate", "valor": lambda j: j["win_rate"]},
    "partidos": {"etiqueta": "Partidos jugados", "valor": lambda j: j["pj"]},
    "torneos": {"etiqueta": "Torneos jugados", "valor": lambda j: j["torneos_jugados"]},
}

ORDEN_POR_DEFECTO = "nombre"


def obtener(orden=ORDEN_POR_DEFECTO, descendente=False, incluir_ocultos=False):
    jugadores = api.get(
        "/jugadores", **({"incluir_ocultos": "si"} if incluir_ocultos else {})
    )
    historico = {f["jugador_id"]: f for f in api.get("/torneos/tabla-historica")}

    enriquecidos = [_con_datos(j, historico.get(j["id"])) for j in jugadores]

    if orden not in ORDENES:
        orden = ORDEN_POR_DEFECTO

    return sorted(
        enriquecidos, key=ORDENES[orden]["valor"], reverse=descendente
    )


def _con_datos(jugador, fila_historica):
    """
    Combina al jugador con sus números.

    Los que nunca jugaron no están en la tabla histórica: se los completa
    con ceros en vez de dejarlos afuera, que los haría desaparecer del
    listado justo cuando más falta hace verlos -- recién cargados.
    """
    if fila_historica is None:
        fila_historica = {"pj": 0, "pg": 0, "win_rate": 0,
                          "torneos_jugados": 0, "rating": 1000}

    return {
        **jugador,
        "pj": fila_historica["pj"],
        "pg": fila_historica["pg"],
        "win_rate": fila_historica["win_rate"],
        "torneos_jugados": fila_historica["torneos_jugados"],
        "rating": fila_historica.get("rating", 1000),
    }
