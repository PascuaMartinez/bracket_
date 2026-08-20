"""
Armado del fixture de un torneo.

Genera los enfrentamientos y en qué jornada se juega cada uno.
"""


def fixture_round_robin(jugadores_ids):
    """
    Todos contra todos, repartido en jornadas.

    Devuelve una lista de jornadas, y cada jornada es una lista de pares
    (jugador1, jugador2). La condición que hace esto no trivial: dentro de
    una jornada nadie puede aparecer dos veces, porque no puede jugar dos
    partidos al mismo tiempo.

    Se usa el método del círculo: se fija un jugador y los demás rotan
    alrededor. En cada vuelta se enfrenta al fijo con el que le quedó
    enfrente, y a los demás de a pares desde los extremos hacia el centro.
    Con N jugadores hacen falta N-1 jornadas (N si es impar, porque en
    cada una alguien descansa).

    La alternativa ingenua -- generar todas las combinaciones y después
    acomodarlas en jornadas -- obliga a resolver a mano el problema de que
    nadie se repita. Acá esa propiedad sale sola de cómo rota el círculo.
    """
    jugadores = list(jugadores_ids)

    # Con cantidad impar se agrega un lugar vacío: el que queda enfrentado
    # a ese hueco es el que descansa esa jornada. Así el algoritmo trabaja
    # siempre con una cantidad par, sin casos especiales.
    hay_descanso = len(jugadores) % 2 == 1
    if hay_descanso:
        jugadores.append(None)

    cantidad = len(jugadores)
    jornadas = []

    for _ in range(cantidad - 1):
        partidos_jornada = []
        for i in range(cantidad // 2):
            local = jugadores[i]
            visitante = jugadores[cantidad - 1 - i]
            # El par que incluye el hueco es el descanso: no es un partido.
            if local is not None and visitante is not None:
                partidos_jornada.append((local, visitante))
        jornadas.append(partidos_jornada)

        # La rotación: el primero queda fijo y el resto gira una posición.
        # Es lo que garantiza que en la próxima jornada todos tengan un
        # rival distinto.
        jugadores = [jugadores[0]] + [jugadores[-1]] + jugadores[1:-1]

    return jornadas
