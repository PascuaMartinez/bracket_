"""
Estadísticas de un jugador.

Se calculan recorriendo todos sus partidos. Casi todas devuelven listas y
no un único resultado: preguntar "contra quién ganó más" puede tener dos
respuestas legítimas si empató entre dos rivales, y elegir una arbitraria
sería inventar un desempate que no existe.
"""
from services import configuracion_service
from repositories import jugador_repository, partido_repository, torneo_repository


class JugadorNoEncontradoError(Exception):
    pass


def obtener_estadisticas(jugador_id):
    jugador = jugador_repository.obtener_por_id(jugador_id)
    if jugador is None:
        raise JugadorNoEncontradoError(f"No existe el jugador {jugador_id}")

    # Solo los torneos terminados: uno a medio jugar daría estadísticas
    # que cambian con cada resultado que se carga.
    torneos = [t for t in torneo_repository.obtener_todos() if t.estado == "finalizado"]
    nombres = {j.id: j.nombre for j in jugador_repository.obtener_todos()}

    partidos = []
    for torneo in torneos:
        for p in partido_repository.obtener_por_torneo(torneo.id):
            if p.estado != "finalizado" or p.ganador_id is None:
                continue
            if p.es_pase_libre:
                # No se jugó: contarlo como victoria inflaría el récord de
                # quien tuvo la suerte de que el cuadro no cerrara justo.
                continue
            if jugador_id in (p.jugador1_id, p.jugador2_id):
                partidos.append(p)

    estadisticas = {
        "torneos_jugados": _contar_torneos(partidos),
        **_record(partidos, jugador_id),
        **_rivales(partidos, jugador_id, nombres),
        "mejor_racha": _mejor_racha(partidos, jugador_id),
    }

    # La identidad no se filtra: sin nombre ni id, la respuesta no sirve
    # para nada aunque se escondan todas las estadísticas.
    return {
        "jugador_id": jugador_id,
        "nombre": jugador.nombre,
        **configuracion_service.filtrar_ocultas(estadisticas, "jugador"),
    }


def _contar_torneos(partidos):
    return len({p.torneo_id for p in partidos})


def _record(partidos, jugador_id):
    ganados = sum(1 for p in partidos if p.ganador_id == jugador_id)
    jugados = len(partidos)
    return {
        "partidos_jugados": jugados,
        "partidos_ganados": ganados,
        "partidos_perdidos": jugados - ganados,
        "win_rate": round(ganados / jugados, 3) if jugados else 0,
    }


def _rivales(partidos, jugador_id, nombres):
    """Con quién jugó, contra quién ganó más y contra quién perdió más."""
    por_rival = {}
    for p in partidos:
        rival_id = p.jugador2_id if p.jugador1_id == jugador_id else p.jugador1_id
        datos = por_rival.setdefault(rival_id, {
            "jugador_id": rival_id,
            "nombre": nombres.get(rival_id),
            "jugados": 0, "ganados": 0, "perdidos": 0,
        })
        datos["jugados"] += 1
        if p.ganador_id == jugador_id:
            datos["ganados"] += 1
        else:
            datos["perdidos"] += 1

    rivales = list(por_rival.values())
    for r in rivales:
        r["win_rate"] = round(r["ganados"] / r["jugados"], 3) if r["jugados"] else 0

    return {
        "rival_mas_frecuente": _todos_los_maximos(rivales, lambda r: r["jugados"]),
        "a_quien_le_gano_mas": _todos_los_maximos(rivales, lambda r: r["ganados"]),
        "contra_quien_perdio_mas": _todos_los_maximos(rivales, lambda r: r["perdidos"]),
        "matchup_mas_parejo": _matchup_mas_parejo(rivales),
    }


# Para hablar de una rivalidad pareja hace falta un mínimo de partidos:
# con uno o dos, el resultado es azar y no una tendencia.
MINIMO_PARTIDOS_PARA_MATCHUP = 3


def _matchup_mas_parejo(rivales):
    """
    Contra qué rival la cosa está más pareja.

    Lo intuitivo sería medir la diferencia entre ganados y perdidos, pero
    eso da resultados equivocados: un 0-3 tiene diferencia 3 y un 4-6
    tiene diferencia 2, así que el 0-3 -- que es una paliza -- ganaría
    contra el 4-6, que es una rivalidad genuinamente pareja.

    El problema es que la diferencia bruta ignora cuántos partidos se
    jugaron. Lo que corresponde medir es qué tan cerca del 50% está el
    win rate: 0-3 da 0% (lejísimos) y 4-6 da 40% (cerca), que es lo que
    uno espera leer ahí.

    Ante igual cercanía al 50%, gana el que jugó más partidos: un 5-5
    dice más de una rivalidad pareja que un 1-1.
    """
    candidatos = [r for r in rivales if r["jugados"] >= MINIMO_PARTIDOS_PARA_MATCHUP]
    if not candidatos:
        return []

    def distancia_al_medio(rival):
        return abs(rival["win_rate"] - 0.5)

    mas_cercano = min(distancia_al_medio(r) for r in candidatos)
    empatados = [r for r in candidatos if distancia_al_medio(r) == mas_cercano]

    max_jugados = max(r["jugados"] for r in empatados)
    return [r for r in empatados if r["jugados"] == max_jugados]


def _mejor_racha(partidos, jugador_id):
    """La seguidilla de victorias más larga, en orden cronológico.

    Se ordena por torneo y por el orden dentro del torneo: la fecha sola
    no alcanza porque todos los partidos de una noche la comparten."""
    en_orden = sorted(partidos, key=lambda p: (p.torneo_id, p.orden or 0))

    mejor = 0
    actual = 0
    for p in en_orden:
        actual = actual + 1 if p.ganador_id == jugador_id else 0
        mejor = max(mejor, actual)
    return mejor


def _todos_los_maximos(elementos, clave):
    """
    Devuelve TODOS los que empatan en el máximo, no uno solo.

    Si alguien jugó la misma cantidad de veces contra dos rivales, las dos
    respuestas son igual de ciertas. Devolver una sola obligaría a inventar
    un desempate -- el orden alfabético, el id más bajo -- que no significa
    nada y haría que el resultado dependa de un detalle arbitrario.

    Los que están en cero no cuentan: "contra quién perdió más" no debería
    devolver a todos los rivales invictos cuando el jugador no perdió nunca.
    """
    if not elementos:
        return []
    maximo = max(clave(e) for e in elementos)
    if maximo == 0:
        return []
    return [e for e in elementos if clave(e) == maximo]
