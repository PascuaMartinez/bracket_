"""
Tabla de posiciones de un torneo.

Se calcula a partir de los partidos jugados, no se guarda. Guardarla
obligaría a mantenerla sincronizada cada vez que se carga o se corrige un
resultado, y cualquier olvido dejaría la tabla mintiendo. Calcularla al
momento es más lento pero no puede quedar desactualizada.
"""
from repositories import partido_repository, torneo_repository


def calcular_tabla(torneo_id):
    """
    Devuelve la tabla ordenada, de primero a último.

    Cada fila trae el puesto, los partidos jugados, ganados y perdidos, el
    win rate y los puntos.
    """
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
