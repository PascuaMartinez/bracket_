"""
Tabla final de un torneo de rey de la cancha.

El formato: el que gana se queda en cancha y el que pierde una vida vuelve
al final de la cola. Termina cuando queda uno solo con vidas.

Ordenar el resultado no es obvio. Quién duró más no alcanza: alguien
puede sobrevivir mucho rato sin ganar nunca, simplemente porque la cola
es larga y le tocan pocos turnos. Y contar victorias tampoco, porque no
distingue al que ganó cuatro seguidas del que ganó cuatro sueltas -- y en
este formato son cosas muy distintas.
"""
# Cuánto pesa cada cosa en el puesto final. Las rachas mandan; qué tan
# lejos llegaste alcanza para desempatar entre dos que hicieron rachas
# parecidas, sin llegar a decidir el orden por sí solo.
PESO_RACHA = 0.8
PESO_POSICION = 0.2


def puntos_de_racha(largo):
    """
    Una racha de N victorias seguidas vale N².

    Es la decisión central del formato. La razón es que cada victoria
    seguida es más difícil que la anterior: el que está en cancha se
    desgasta y enfrenta rivales descansados, uno atrás de otro. Una escala
    lineal trataría igual a cuatro victorias sueltas que a cuatro
    seguidas, cuando aguantar cuatro seguidas es mucho más mérito.

    Con el cuadrado, dos rachas de 2 dan 8 y una sola racha de 4 da 16.
    """
    return largo * largo


def calcular_puntos_racha(resultados):
    """Suma el valor de todas las rachas de un jugador.

    resultados es una lista de booleanos en orden cronológico: True si
    ganó ese partido."""
    total = 0
    racha_actual = 0
    for gano in resultados:
        if gano:
            racha_actual += 1
        else:
            total += puntos_de_racha(racha_actual)
            racha_actual = 0
    # La racha que quedaba abierta al terminar también cuenta: el campeón
    # nunca pierde, así que sin esto su mejor racha no sumaría nada.
    total += puntos_de_racha(racha_actual)
    return total


def calcular_tabla(jugadores):
    """
    Ordena a los jugadores y les asigna puesto.

    Cada jugador es un dict con: jugador_id, nombre, puntos_racha,
    orden_eliminacion (None si nunca lo eliminaron) y eliminado.

    El campeón siempre es primero, sin importar los números: ganó el
    torneo, y una fórmula que lo pusiera segundo estaría midiendo mal.
    """
    if not jugadores:
        return []

    campeon = next((j for j in jugadores if not j["eliminado"]), None)
    eliminados = [j for j in jugadores if j["eliminado"]]

    for jugador in eliminados:
        jugador["score"] = _score(jugador, eliminados)

    # De mayor a menor score. El orden de eliminación desempata al final
    # para que el resultado sea estable y no dependa del orden en que
    # vengan de la base.
    eliminados.sort(key=lambda j: (-j["score"], -(j["orden_eliminacion"] or 0)))

    tabla = ([campeon] if campeon else []) + eliminados

    # Puesto denso sobre el score: los que empatan comparten puesto.
    puesto = 0
    score_anterior = None
    for i, jugador in enumerate(tabla):
        if i == 0:
            puesto = 1
            score_anterior = jugador.get("score")
        else:
            score = round(jugador.get("score", 0), 9)
            if score != score_anterior:
                puesto += 1
                score_anterior = score
        jugador["puesto"] = puesto

    return tabla


def _score(jugador, eliminados):
    """
    Combina las dos medidas, cada una normalizada a una escala de 0 a 1.

    Se normaliza porque son magnitudes distintas: los puntos de racha
    pueden llegar a 25 y el orden de eliminación a 8. Sin llevarlas a la
    misma escala, la de números más grandes dominaría el resultado sin
    importar los pesos que se le pongan.

    Al normalizar, lo que se mide es cómo le fue a cada uno RESPECTO A LOS
    DEMÁS de ese torneo, que es lo que corresponde comparar.
    """
    max_racha = max((j["puntos_racha"] for j in eliminados), default=0)
    max_orden = max((j["orden_eliminacion"] or 0 for j in eliminados), default=0)

    racha_normalizada = jugador["puntos_racha"] / max_racha if max_racha else 0
    orden_normalizado = (jugador["orden_eliminacion"] or 0) / max_orden if max_orden else 0

    return PESO_RACHA * racha_normalizada + PESO_POSICION * orden_normalizado
