"""
Estadísticas de un personaje.

Todo lo que se puede saber sobre cómo se usó: cuántas veces, con qué
resultado, quién lo elige, y contra qué personajes le va bien o mal.

Depende de que se haya registrado qué personaje usó cada uno al cargar el
resultado, que es opcional. Las estadísticas que no tienen datos
devuelven cero o lista vacía en vez de fallar.
"""
from services import configuracion_service
from repositories import (
    jugador_repository, partido_repository, peleador_repository, torneo_repository,
)

# Para "contra quién le va peor" hace falta un mínimo de enfrentamientos.
# Sin esto, un personaje contra el que se perdió una única vez aparecería
# como el peor rival, y eso no dice nada.
MINIMO_ENFRENTAMIENTOS = 3


class PeleadorNoEncontradoError(Exception):
    pass


def obtener_estadisticas(peleador_id):
    peleador = peleador_repository.obtener_por_id(peleador_id)
    if peleador is None:
        raise PeleadorNoEncontradoError(f"No existe el peleador {peleador_id}")

    apariciones = _apariciones(peleador_id)

    estadisticas = {
        **_uso(apariciones),
        **_quien_lo_usa(apariciones),
        **_enfrentamientos(apariciones, peleador_id),
        **_rachas_y_barridas(apariciones),
    }

    return {
        "peleador_id": peleador_id,
        "nombre": peleador.nombre,
        **configuracion_service.filtrar_ocultas(estadisticas, "peleador"),
    }


def _apariciones(peleador_id):
    """
    Cada vez que el personaje entró a un partido, con su contexto.

    Un partido genera hasta dos apariciones -- una por cada lado -- y si
    los dos jugadores lo eligieron, genera dos del mismo personaje.
    """
    torneos = [t for t in torneo_repository.obtener_todos() if t.estado == "finalizado"]
    nombres_jugador = {j.id: j.nombre for j in jugador_repository.obtener_todos()}
    nombres_peleador = {p.id: p.nombre for p in peleador_repository.obtener_todos()}

    apariciones = []
    for torneo in torneos:
        for p in partido_repository.obtener_por_torneo(torneo.id):
            if p.estado != "finalizado" or p.ganador_id is None or p.es_pase_libre:
                continue

            for lado, contrario in ((1, 2), (2, 1)):
                if getattr(p, f"jugador{lado}_peleador_id") != peleador_id:
                    continue
                jugador_id = getattr(p, f"jugador{lado}_id")
                apariciones.append({
                    "jugador_id": jugador_id,
                    "jugador_nombre": nombres_jugador.get(jugador_id),
                    "rival_peleador_id": getattr(p, f"jugador{contrario}_peleador_id"),
                    "rival_peleador_nombre": nombres_peleador.get(
                        getattr(p, f"jugador{contrario}_peleador_id")
                    ),
                    "gano": p.ganador_id == jugador_id,
                    "rondas": p.rondas_jugadas,
                    "torneo_id": torneo.id,
                    "orden": p.orden or 0,
                })
    return apariciones


def _uso(apariciones):
    usos = len(apariciones)
    ganados = sum(1 for a in apariciones if a["gano"])
    return {
        "veces_usado": usos,
        "victorias": ganados,
        "derrotas": usos - ganados,
        "win_rate": round(ganados / usos, 3) if usos else 0,
        "torneos_distintos": len({a["torneo_id"] for a in apariciones}),
    }


def _quien_lo_usa(apariciones):
    conteo = {}
    for a in apariciones:
        datos = conteo.setdefault(a["jugador_id"], {
            "jugador_id": a["jugador_id"], "nombre": a["jugador_nombre"], "veces": 0,
        })
        datos["veces"] += 1
    return {"mas_usado_por": _todos_los_maximos(conteo.values(), lambda d: d["veces"])}


def _enfrentamientos(apariciones, peleador_id):
    """Contra qué personajes se enfrentó, y cómo le fue con cada uno."""
    por_rival = {}
    espejos = 0

    for a in apariciones:
        rival = a["rival_peleador_id"]
        if rival is None:
            continue
        if rival == peleador_id:
            espejos += 1
            continue

        datos = por_rival.setdefault(rival, {
            "peleador_id": rival, "nombre": a["rival_peleador_nombre"],
            "jugados": 0, "ganados": 0,
        })
        datos["jugados"] += 1
        if a["gano"]:
            datos["ganados"] += 1

    for datos in por_rival.values():
        datos["perdidos"] = datos["jugados"] - datos["ganados"]
        datos["win_rate"] = round(datos["ganados"] / datos["jugados"], 3)

    # Solo los que se enfrentaron lo suficiente: con uno o dos partidos,
    # el win rate no dice nada todavía.
    con_historial = [d for d in por_rival.values()
                     if d["jugados"] >= MINIMO_ENFRENTAMIENTOS]

    return {
        # Los espejos se cuentan en partidos, no en apariciones: un partido
        # donde los dos eligieron el mismo personaje genera dos apariciones
        # pero es un solo espejo.
        "espejos": espejos // 2,
        "peor_enemigo": _todos_los_minimos(con_historial, lambda d: d["win_rate"]),
        "victima_favorita": _todos_los_maximos(con_historial, lambda d: d["win_rate"]),
    }


def _rachas_y_barridas(apariciones):
    """
    Las barridas (2-0) y los partidos cerrados (2-1) distinguen al
    personaje que arrasa del que gana sufriendo. Solo cuentan los partidos
    donde se registró el dato de rondas, que es opcional.
    """
    con_rondas = [a for a in apariciones if a["rondas"]]

    en_orden = sorted(apariciones, key=lambda a: (a["torneo_id"], a["orden"]))
    mejor_racha = 0
    racha = 0
    for a in en_orden:
        racha = racha + 1 if a["gano"] else 0
        mejor_racha = max(mejor_racha, racha)

    return {
        "barridas_a_favor": sum(1 for a in con_rondas if a["gano"] and a["rondas"] == 2),
        "barridas_en_contra": sum(1 for a in con_rondas if not a["gano"] and a["rondas"] == 2),
        "partidos_cerrados": sum(1 for a in con_rondas if a["rondas"] == 3),
        "mejor_racha": mejor_racha,
    }


def _todos_los_maximos(elementos, clave):
    """Devuelve todos los que empatan en el máximo: elegir uno sería
    inventar un desempate que no existe."""
    elementos = list(elementos)
    if not elementos:
        return []
    maximo = max(clave(e) for e in elementos)
    return [e for e in elementos if clave(e) == maximo]


def _todos_los_minimos(elementos, clave):
    elementos = list(elementos)
    if not elementos:
        return []
    minimo = min(clave(e) for e in elementos)
    return [e for e in elementos if clave(e) == minimo]
