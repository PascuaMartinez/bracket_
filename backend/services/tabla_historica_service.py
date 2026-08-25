"""
Tabla histórica: el acumulado de todos los torneos finalizados.

Es el producto real del sistema. Un torneo puntual se olvida a la semana;
lo que ordena al grupo es el acumulado, y es lo que se mira para saber
cómo viene cada uno.
"""
from repositories import partido_repository, torneo_repository
from services import cache, rating_service, tabla_service

# Cuántos puntos da cada puesto. La escala no es lineal a propósito:
# la diferencia entre salir primero y segundo pesa más que entre quinto y
# sexto, que es como se siente ganar un torneo. Del sexto en adelante
# todos suman 1: presentarse cuenta, y ese punto premia la constancia de
# venir siempre aunque no se gane.
PUNTOS_POR_PUESTO = {1: 8, 2: 7, 3: 6, 4: 4, 5: 2}
PUNTOS_PARTICIPACION = 1

# Puntos por cada partido ganado, para desempatar. Vale más que un punto
# de participación pero menos que un puesto: sirve para separar a dos que
# terminaron parecido, sin que alguien que ganó muchos partidos en
# torneos flojos supere a quien ganó un torneo.
PUNTOS_POR_VICTORIA = 3


def puntos_de_puesto(puesto):
    return PUNTOS_POR_PUESTO.get(puesto, PUNTOS_PARTICIPACION)


def calcular_tabla_historica():
    """Devuelve el acumulado, usando el cache si está vigente."""
    return cache.obtener("tabla-historica", _calcular_tabla_historica)


def _calcular_tabla_historica():
    """
    Suma lo que hizo cada jugador en todos los torneos finalizados.

    Cada fila trae los puntos acumulados, en cuántos torneos participó,
    su récord de partidos y las insignias -- el puesto que sacó en cada
    torneo, en orden cronológico, para leer de un vistazo el recorrido.
    """
    torneos = [t for t in torneo_repository.obtener_todos() if t.estado == "finalizado"]
    # De más viejo a más nuevo: las insignias se leen como una línea de
    # tiempo, así que el orden importa.
    torneos.sort(key=lambda t: (t.fecha, t.id))

    # Todo de una vez, en dos consultas, en vez de tres por cada torneo.
    # Antes esto crecía con la cantidad de torneos: con 20 eran 61
    # consultas. Ahora son 3, tenga los torneos que tenga.
    ids = [t.id for t in torneos]
    participantes_por_torneo = torneo_repository.obtener_participantes_de_varios(ids)
    partidos_por_torneo = partido_repository.obtener_de_varios_torneos(ids)

    acumulado = {}

    for torneo in torneos:
        tabla = tabla_service.calcular_tabla(
            torneo.id,
            torneo=torneo,
            participantes=participantes_por_torneo.get(torneo.id, []),
            partidos=partidos_por_torneo.get(torneo.id, []),
        )
        for fila in tabla:
            jugador = acumulado.setdefault(fila["jugador_id"], {
                "jugador_id": fila["jugador_id"],
                "nombre": fila["nombre"],
                "puntos": 0,
                "torneos_jugados": 0,
                "pj": 0, "pg": 0, "pp": 0,
                "puntos_victoria": 0,
                "insignias": [],
            })
            jugador["puntos"] += puntos_de_puesto(fila["puesto"])
            jugador["torneos_jugados"] += 1
            jugador["pj"] += fila["pj"]
            jugador["pg"] += fila["pg"]
            jugador["pp"] += fila["pp"]
            jugador["puntos_victoria"] += fila["pg"] * PUNTOS_POR_VICTORIA
            jugador["insignias"].append({
                "torneo_id": torneo.id,
                "torneo_nombre": torneo.nombre,
                "puesto": fila["puesto"],
            })

    filas = list(acumulado.values())

    # El rating se calcula sobre todos los partidos juntos, no torneo por
    # torneo: el modelo necesita el historial completo para estimar bien
    # quién enfrentó a quién.
    ratings = rating_service.calcular_ratings(
        [f["jugador_id"] for f in filas],
        _enfrentamientos(partidos_por_torneo),
    )

    for fila in filas:
        fila["win_rate"] = round(fila["pg"] / fila["pj"], 3) if fila["pj"] else 0
        fila["rating"] = ratings.get(fila["jugador_id"], rating_service.RATING_BASE)

    # Puntos, después puntos de victoria, después win rate. Tres criterios
    # porque con dos los empates son frecuentes: si dos jugaron los mismos
    # torneos y salieron parecido, la tabla no debería dejarlos indistintos.
    filas.sort(key=lambda f: (-f["puntos"], -f["puntos_victoria"], -f["win_rate"]))

    _asignar_puestos(filas)
    return filas


def _asignar_puestos(filas_ordenadas):
    """Puesto denso sobre los tres criterios: comparten puesto solo si
    empatan en todo, no solo en puntos."""
    puesto_actual = 0
    clave_anterior = None
    for fila in filas_ordenadas:
        clave = (fila["puntos"], fila["puntos_victoria"], fila["win_rate"])
        if clave != clave_anterior:
            puesto_actual += 1
            clave_anterior = clave
        fila["puesto"] = puesto_actual


def _enfrentamientos(partidos_por_torneo):
    """Los partidos como pares (ganador, perdedor), que es lo único que el
    modelo necesita saber."""
    pares = []
    for partidos in partidos_por_torneo.values():
        for p in partidos:
            if p.estado != "finalizado" or p.ganador_id is None or p.es_pase_libre:
                continue
            perdedor = p.jugador2_id if p.ganador_id == p.jugador1_id else p.jugador1_id
            if perdedor is not None:
                pares.append((p.ganador_id, perdedor))
    return pares
