"""
Navegación entre elementos de una lista.

Estando en el detalle de un jugador, poder pasar al siguiente sin volver
al listado. Mirar a cinco jugadores seguidos son cinco viajes de ida y
vuelta que se ahorran.
"""


def vecinos(elementos, actual_id):
    """
    Cuál viene antes y cuál después del elemento actual.

    Devuelve (anterior, siguiente), cada uno con id y nombre, o None.

    La navegación es CÍCLICA: desde el último, "siguiente" lleva al
    primero. Sin eso, las flechas se apagan en los extremos y quien está
    recorriendo la lista se queda trabado sin entender por qué -- sobre
    todo en una lista corta, donde llegar al final pasa enseguida.

    El orden es el mismo del listado: si en pantalla están alfabéticos,
    las flechas tienen que seguir ese orden y no otro, o el recorrido se
    vuelve impredecible.
    """
    if not elementos:
        return None, None

    posicion = next(
        (i for i, e in enumerate(elementos) if e["id"] == actual_id), None
    )
    if posicion is None:
        return None, None   # el elemento no está en la lista

    # Con uno solo, no hay a dónde ir: devolver el mismo elemento haría
    # que las flechas parezcan funcionar sin llevar a ningún lado.
    if len(elementos) == 1:
        return None, None

    anterior = elementos[posicion - 1]           # con posición 0, cae en el último
    siguiente = elementos[(posicion + 1) % len(elementos)]

    return _resumen(anterior), _resumen(siguiente)


def _resumen(elemento):
    """Solo lo que la flecha necesita mostrar: a dónde va y cómo se llama.

    Se recorta a propósito en vez de pasar el elemento entero: la
    plantilla no debería tener acceso a datos que no va a usar."""
    return {"id": elemento["id"], "nombre": elemento["nombre"]}
