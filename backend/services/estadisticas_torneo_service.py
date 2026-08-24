"""
Estadísticas de un torneo puntual.

La tabla dice quién ganó; esto dice cómo se dio. Cuántas barridas hubo,
qué partido fue el más peleado, quién arrasó y quién sufrió cada
victoria.

Son las que le dan carácter a un torneo cuando se lo mira meses después:
"ese fue el de las cinco barridas seguidas" se recuerda mejor que una
tabla de posiciones.
"""
from repositories import jugador_repository, partido_repository, torneo_repository


class TorneoNoEncontradoError(Exception):
    pass


def obtener_estadisticas(torneo_id):
    torneo = torneo_repository.obtener_por_id(torneo_id)
    if torneo is None:
        raise TorneoNoEncontradoError(f"No existe el torneo {torneo_id}")

    partidos = [
        p for p in partido_repository.obtener_por_torneo(torneo_id)
        # Los pases libres no se jugaron: contarlos como partidos
        # inflaría todos los números del torneo.
        if p.estado == "finalizado" and p.ganador_id is not None and not p.es_pase_libre
    ]
    nombres = {j.id: j.nombre for j in jugador_repository.obtener_todos()}
    participantes = torneo_repository.obtener_participantes(torneo_id)

    return {
        "torneo_id": torneo_id,
        "cantidad_jugadores": len(participantes),
        "partidos_jugados": len(partidos),
        **_rondas(partidos),
        **_destacados(partidos, nombres),
    }


def _rondas(partidos):
    """
    Cuántos partidos se definieron rápido y cuántos se pelearon.

    Solo cuentan los que tienen el dato de rondas, que es opcional. Se
    informa además cuántos lo tienen: sin eso, "2 barridas" no dice nada
    -- puede ser 2 de 3 partidos o 2 de 40.
    """
    con_dato = [p for p in partidos if p.rondas_jugadas]

    return {
        "partidos_con_rondas": len(con_dato),
        "barridas": sum(1 for p in con_dato if p.rondas_jugadas == 2),
        "cerrados": sum(1 for p in con_dato if p.rondas_jugadas == 3),
    }


def _destacados(partidos, nombres):
    """Quién ganó más y quién perdió más dentro de este torneo."""
    ganados = {}
    perdidos = {}

    for p in partidos:
        perdedor_id = p.jugador2_id if p.ganador_id == p.jugador1_id else p.jugador1_id
        ganados[p.ganador_id] = ganados.get(p.ganador_id, 0) + 1
        perdidos[perdedor_id] = perdidos.get(perdedor_id, 0) + 1

    def lista(conteo):
        return [
            {"jugador_id": jid, "nombre": nombres.get(jid), "veces": veces}
            for jid, veces in conteo.items()
        ]

    return {
        "mas_victorias": _todos_los_maximos(lista(ganados)),
        "mas_derrotas": _todos_los_maximos(lista(perdidos)),
        # La racha más larga del torneo: es lo que se recuerda después.
        "mejor_racha": _mejor_racha_del_torneo(partidos, nombres),
    }


def _mejor_racha_del_torneo(partidos, nombres):
    """
    La seguidilla de victorias más larga que logró alguien en el torneo.

    Se calcula por jugador, recorriendo sus partidos en el orden en que se
    jugaron. Devuelve lista porque puede haber empate, y elegir uno sería
    inventar un desempate.
    """
    en_orden = sorted(partidos, key=lambda p: p.orden or 0)

    rachas = {}
    actuales = {}
    for p in en_orden:
        perdedor_id = p.jugador2_id if p.ganador_id == p.jugador1_id else p.jugador1_id
        actuales[p.ganador_id] = actuales.get(p.ganador_id, 0) + 1
        rachas[p.ganador_id] = max(rachas.get(p.ganador_id, 0), actuales[p.ganador_id])
        actuales[perdedor_id] = 0

    if not rachas:
        return []

    mejor = max(rachas.values())
    if mejor < 2:
        # Una "racha" de una victoria no es una racha: la tendrían todos
        # los que ganaron algún partido.
        return []

    return [
        {"jugador_id": jid, "nombre": nombres.get(jid), "veces": largo}
        for jid, largo in rachas.items() if largo == mejor
    ]


def _todos_los_maximos(elementos):
    """Todos los que empatan en el máximo. Los que están en cero no
    cuentan: 'quién perdió más' no debería listar a nadie si no hubo
    partidos."""
    if not elementos:
        return []
    maximo = max(e["veces"] for e in elementos)
    if maximo == 0:
        return []
    return [e for e in elementos if e["veces"] == maximo]
