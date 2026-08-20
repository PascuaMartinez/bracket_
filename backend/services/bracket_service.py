"""
Armado del cuadro de eliminación directa.

A diferencia del round-robin, acá solo se puede generar la primera ronda:
quién juega en la segunda depende de quién gane en la primera. El resto
del cuadro se va armando a medida que se cargan resultados.
"""
import math


def cantidad_de_rondas(cantidad_jugadores):
    """Cuántas rondas hacen falta hasta que quede un solo jugador.

    Con 8 son 3 (8 -> 4 -> 2 -> 1). Si la cantidad no es potencia de dos
    se redondea para arriba: con 6 hacen falta 3 rondas igual, porque hay
    que llegar a un cuadro de 8."""
    return math.ceil(math.log2(cantidad_jugadores))


def sembrar_primera_ronda(jugadores_ids):
    """
    Arma los cruces de la primera ronda.

    Devuelve una lista de pares. Cuando falta uno para completar el par,
    el segundo lugar viene en None: ese jugador pasa de ronda sin jugar.

    La siembra enfrenta al primero con el último, al segundo con el
    anteúltimo, y así hacia el centro. Se hace de esa forma y no en el
    orden en que vienen para que los mejores sembrados no se crucen entre
    sí en la primera ronda -- si el 1 y el 2 se enfrentan de entrada, uno
    de los dos queda afuera enseguida y el cuadro pierde interés.

    Se asume que la lista viene ordenada de mejor a peor sembrado (por
    ejemplo, según la tabla histórica). Si viene sin orden, el resultado
    sigue siendo un cuadro válido, solo que los cruces son arbitrarios.
    """
    jugadores = list(jugadores_ids)

    # Se completa hasta la potencia de dos más cercana con lugares vacíos.
    # Los que quedan enfrentados a un vacío pasan de ronda sin jugar, que
    # es la forma estándar de resolver una cantidad que no es potencia de
    # dos: la alternativa -- hacer jugar una ronda previa solo a algunos --
    # les daría a esos un partido de desventaja frente al resto.
    tamano_cuadro = 2 ** cantidad_de_rondas(len(jugadores))
    jugadores += [None] * (tamano_cuadro - len(jugadores))

    cruces = []
    for i in range(tamano_cuadro // 2):
        cruces.append((jugadores[i], jugadores[tamano_cuadro - 1 - i]))
    return cruces


def nombre_de_ronda(cantidad_partidos):
    """El nombre que se le dice a una ronda según cuántos partidos tiene.

    Se deduce de la cantidad y no se guarda: así el mismo número de ronda
    puede ser 'cuartos' en un torneo de 8 y 'octavos' en uno de 16, sin
    que haya que recalcular nada al agregar jugadores."""
    nombres = {1: "Final", 2: "Semifinal", 4: "Cuartos de final", 8: "Octavos de final"}
    return nombres.get(cantidad_partidos, f"Ronda de {cantidad_partidos * 2}")
