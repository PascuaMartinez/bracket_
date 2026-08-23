"""
Tabla de posiciones de un torneo.

Se calcula a partir de los partidos jugados, no se guarda. Guardarla
obligaría a mantenerla sincronizada cada vez que se carga o se corrige un
resultado, y cualquier olvido dejaría la tabla mintiendo. Calcularla al
momento es más lento pero no puede quedar desactualizada.
"""
from repositories import (
    grupo_repository, partido_repository, torneo_repository, vidas_repository,
)
from services import rey_de_la_cancha_service


def calcular_tabla(torneo_id):
    """
    Tabla de posiciones de un torneo, sea cual sea su formato.

    Cada formato define el puesto a su manera y no hay uno que sirva para
    los tres: en todos contra todos ordena quién ganó más partidos, en
    eliminación quién llegó más lejos en el cuadro, y en rey de la cancha
    una fórmula propia. Lo que sí comparten es la FORMA del resultado --
    una lista de filas con puesto, nombre y récord -- y es eso lo que
    permite que el acumulado histórico las trate a todas igual sin saber
    de qué formato vienen.
    """
    torneo = torneo_repository.obtener_por_id(torneo_id)
    if torneo is None:
        return []

    if torneo.modo == "eliminacion":
        return _tabla_eliminacion(torneo_id)
    if torneo.modo == "rey_de_la_cancha":
        return _tabla_rey_de_la_cancha(torneo_id)
    if torneo.modo == "grupos_eliminacion":
        # La tabla general del torneo sale del cuadro: quién llegó más
        # lejos. Las tablas por grupo son de la fase previa y se consultan
        # aparte.
        return _tabla_eliminacion(torneo_id)
    return _tabla_todos_contra_todos(torneo_id)


def _tabla_todos_contra_todos(torneo_id):
    """Ordena por partidos ganados."""
    participantes = torneo_repository.obtener_participantes(torneo_id)
    partidos = partido_repository.obtener_por_torneo(torneo_id)

    # Arranca con todos en cero: un jugador que todavía no jugó tiene que
    # aparecer en la tabla igual, no ausente hasta que gane algo.
    filas = {
        p["jugador_id"]: {
            "jugador_id": p["jugador_id"],
            "nombre": p["nombre"],
            "pj": 0, "pg": 0, "pp": 0, "puntos": 0,
        }
        for p in participantes
    }

    for partido in partidos:
        if partido.estado != "finalizado" or partido.ganador_id is None:
            continue

        perdedor_id = (
            partido.jugador2_id if partido.ganador_id == partido.jugador1_id
            else partido.jugador1_id
        )

        if partido.ganador_id in filas:
            filas[partido.ganador_id]["pj"] += 1
            filas[partido.ganador_id]["pg"] += 1
            filas[partido.ganador_id]["puntos"] += 1
        if perdedor_id in filas:
            filas[perdedor_id]["pj"] += 1
            filas[perdedor_id]["pp"] += 1

    for fila in filas.values():
        fila["win_rate"] = round(fila["pg"] / fila["pj"], 3) if fila["pj"] else 0

    # Primero por puntos, y entre los que empatan, por win rate. El win
    # rate desempata pero no ordena: alguien con 3 de 3 no puede pasar a
    # otro con 5 de 8, porque ganó menos partidos en total.
    ordenadas = sorted(filas.values(), key=lambda f: (-f["puntos"], -f["win_rate"]))

    _asignar_puestos(ordenadas)
    return ordenadas


def _asignar_puestos(filas_ordenadas):
    """
    Puesto denso: los que empatan en puntos comparten puesto, y el
    siguiente grupo pasa al número que sigue sin saltear.

    O sea 1, 2, 2, 3 -- y no 1, 2, 2, 4. Con pocos jugadores, saltear
    números hace que la tabla se lea mal: si tres empatan en la punta,
    el cuarto siendo '4°' suena peor de lo que fue.
    """
    puesto_actual = 0
    puntos_anteriores = None
    for fila in filas_ordenadas:
        if fila["puntos"] != puntos_anteriores:
            puesto_actual += 1
            puntos_anteriores = fila["puntos"]
        fila["puesto"] = puesto_actual


def _tabla_eliminacion(torneo_id):
    """
    Ordena por hasta dónde llegó cada uno en el cuadro.

    El puesto sale de en qué ronda quedó afuera: el campeón primero, el
    finalista segundo, los que perdieron en semis comparten el tercer
    puesto, y así. Los que cayeron en la misma instancia comparten puesto
    porque el cuadro no los enfrentó entre sí -- decidir cuál de los dos
    semifinalistas eliminados fue "mejor" sería inventar una comparación
    que el torneo nunca hizo.
    """
    participantes = torneo_repository.obtener_participantes(torneo_id)
    partidos = partido_repository.obtener_por_torneo(torneo_id)

    filas = {
        p["jugador_id"]: {
            "jugador_id": p["jugador_id"], "nombre": p["nombre"],
            "pj": 0, "pg": 0, "pp": 0, "ronda_alcanzada": 0,
        }
        for p in participantes
    }

    for partido in partidos:
        if partido.estado != "finalizado" or partido.ganador_id is None:
            continue

        # Hasta qué ronda llegó cada uno: la más alta en la que aparece.
        for jugador_id in (partido.jugador1_id, partido.jugador2_id):
            if jugador_id in filas:
                filas[jugador_id]["ronda_alcanzada"] = max(
                    filas[jugador_id]["ronda_alcanzada"], partido.ronda or 0
                )

        # Los pases libres no cuentan como partido jugado.
        if partido.es_pase_libre:
            continue

        perdedor_id = (
            partido.jugador2_id if partido.ganador_id == partido.jugador1_id
            else partido.jugador1_id
        )
        if partido.ganador_id in filas:
            filas[partido.ganador_id]["pj"] += 1
            filas[partido.ganador_id]["pg"] += 1
        if perdedor_id in filas:
            filas[perdedor_id]["pj"] += 1
            filas[perdedor_id]["pp"] += 1

    ordenadas = sorted(filas.values(), key=lambda f: (-f["ronda_alcanzada"], -f["pg"]))

    for fila in ordenadas:
        fila["puntos"] = fila["pg"]
        fila["win_rate"] = round(fila["pg"] / fila["pj"], 3) if fila["pj"] else 0

    # El puesto se agrupa por ronda alcanzada, no por victorias: los dos
    # semifinalistas eliminados comparten puesto aunque uno haya ganado
    # más partidos antes de llegar ahí.
    puesto = 0
    ronda_anterior = None
    for fila in ordenadas:
        if fila["ronda_alcanzada"] != ronda_anterior:
            puesto += 1
            ronda_anterior = fila["ronda_alcanzada"]
        fila["puesto"] = puesto

    return ordenadas


def _tabla_rey_de_la_cancha(torneo_id):
    """Delega en la fórmula propia del formato (racha² + qué tan lejos
    llegó), y le agrega el récord de partidos que el resto del sistema
    espera encontrar en toda tabla."""
    estado = vidas_repository.obtener_estado(torneo_id)
    partidos = partido_repository.obtener_por_torneo(torneo_id)

    resultados_por_jugador = {j["jugador_id"]: [] for j in estado}
    record = {j["jugador_id"]: {"pj": 0, "pg": 0, "pp": 0} for j in estado}

    for partido in sorted(partidos, key=lambda p: p.orden or 0):
        if partido.estado != "finalizado" or partido.ganador_id is None:
            continue
        perdedor_id = (
            partido.jugador2_id if partido.ganador_id == partido.jugador1_id
            else partido.jugador1_id
        )
        for jugador_id, gano in ((partido.ganador_id, True), (perdedor_id, False)):
            if jugador_id in resultados_por_jugador:
                resultados_por_jugador[jugador_id].append(gano)
                record[jugador_id]["pj"] += 1
                record[jugador_id]["pg" if gano else "pp"] += 1

    jugadores = [{
        "jugador_id": j["jugador_id"],
        "nombre": j["nombre"],
        "puntos_racha": rey_de_la_cancha_service.calcular_puntos_racha(
            resultados_por_jugador[j["jugador_id"]]
        ),
        "orden_eliminacion": j["orden_eliminacion"],
        "eliminado": bool(j["eliminado"]),
    } for j in estado]

    tabla = rey_de_la_cancha_service.calcular_tabla(jugadores)

    for fila in tabla:
        fila.update(record[fila["jugador_id"]])
        fila["puntos"] = fila["puntos_racha"]
        fila["win_rate"] = round(fila["pg"] / fila["pj"], 3) if fila["pj"] else 0

    return tabla


def calcular_tabla_de_grupo(torneo_id, grupo_id):
    """
    Tabla de un grupo puntual.

    Es la misma lógica que todos contra todos, pero mirando solo a los
    jugadores del grupo y los partidos entre ellos. De acá salen los
    clasificados.
    """
    jugadores = grupo_repository.obtener_jugadores(grupo_id)
    ids_del_grupo = {j["jugador_id"] for j in jugadores}

    filas = {
        j["jugador_id"]: {
            "jugador_id": j["jugador_id"], "nombre": j["nombre"],
            "pj": 0, "pg": 0, "pp": 0, "puntos": 0,
        }
        for j in jugadores
    }

    for partido in partido_repository.obtener_por_torneo(torneo_id):
        # Solo los de la fase de grupos (ronda None) y entre jugadores de
        # ESTE grupo: los del cuadro no cuentan para la tabla del grupo.
        if partido.ronda is not None or partido.estado != "finalizado":
            continue
        if partido.jugador1_id not in ids_del_grupo:
            continue

        perdedor_id = (
            partido.jugador2_id if partido.ganador_id == partido.jugador1_id
            else partido.jugador1_id
        )
        filas[partido.ganador_id]["pj"] += 1
        filas[partido.ganador_id]["pg"] += 1
        filas[partido.ganador_id]["puntos"] += 1
        filas[perdedor_id]["pj"] += 1
        filas[perdedor_id]["pp"] += 1

    for fila in filas.values():
        fila["win_rate"] = round(fila["pg"] / fila["pj"], 3) if fila["pj"] else 0

    ordenadas = sorted(filas.values(), key=lambda f: (-f["puntos"], -f["win_rate"]))
    _asignar_puestos(ordenadas)
    return ordenadas
