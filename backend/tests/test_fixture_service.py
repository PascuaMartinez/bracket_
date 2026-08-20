"""
Pruebas del armado del fixture.

Es lógica pura -- entra una lista de jugadores y sale una lista de
jornadas -- así que no necesita base ni mocks. Ese es justamente el
motivo por el que el algoritmo vive en su propio módulo y no adentro del
servicio que lo usa.
"""
from itertools import combinations

import pytest

from services.fixture_service import fixture_round_robin


# Se prueba con muchos tamaños y no con uno solo: los errores de este tipo
# de algoritmo suelen aparecer en un caso puntual (el impar, el chico) y
# pasar desapercibidos en el resto.
TAMANOS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


@pytest.mark.parametrize("cantidad", TAMANOS)
def test_todos_se_enfrentan_exactamente_una_vez(cantidad):
    jugadores = list(range(1, cantidad + 1))

    partidos = [p for jornada in fixture_round_robin(jugadores) for p in jornada]

    # Se comparan como conjuntos sin orden: da igual quién figure primero,
    # (1,2) y (2,1) son el mismo enfrentamiento.
    enfrentamientos = [frozenset(p) for p in partidos]
    esperados = {frozenset(c) for c in combinations(jugadores, 2)}

    assert len(enfrentamientos) == len(set(enfrentamientos)), "hay partidos repetidos"
    assert set(enfrentamientos) == esperados, "faltan o sobran enfrentamientos"


@pytest.mark.parametrize("cantidad", TAMANOS)
def test_nadie_juega_dos_veces_en_la_misma_jornada(cantidad):
    """La condición que hace no trivial al problema: un jugador no puede
    estar en dos partidos de la misma jornada porque no puede jugarlos
    al mismo tiempo."""
    jugadores = list(range(1, cantidad + 1))

    for numero, jornada in enumerate(fixture_round_robin(jugadores), start=1):
        participantes = [jugador for partido in jornada for jugador in partido]
        assert len(participantes) == len(set(participantes)), (
            f"alguien juega dos veces en la jornada {numero}"
        )


@pytest.mark.parametrize("cantidad", TAMANOS)
def test_cantidad_de_partidos(cantidad):
    """Con N jugadores tienen que salir N*(N-1)/2 partidos: cada par se
    enfrenta una vez."""
    jugadores = list(range(1, cantidad + 1))

    partidos = [p for jornada in fixture_round_robin(jugadores) for p in jornada]

    assert len(partidos) == cantidad * (cantidad - 1) // 2


def test_con_cantidad_impar_uno_descansa_por_jornada():
    """Con impares no hay forma de que jueguen todos a la vez: en cada
    jornada tiene que quedar exactamente uno afuera."""
    jugadores = [1, 2, 3, 4, 5]

    jornadas = fixture_round_robin(jugadores)

    for jornada in jornadas:
        jugando = {jugador for partido in jornada for jugador in partido}
        descansando = set(jugadores) - jugando
        assert len(descansando) == 1

    # Y a lo largo del torneo, cada uno descansa exactamente una vez.
    descansos = []
    for jornada in jornadas:
        jugando = {jugador for partido in jornada for jugador in partido}
        descansos.append((set(jugadores) - jugando).pop())
    assert sorted(descansos) == sorted(jugadores)


def test_nadie_se_enfrenta_a_si_mismo():
    for cantidad in TAMANOS:
        jugadores = list(range(1, cantidad + 1))
        for jornada in fixture_round_robin(jugadores):
            for jugador1, jugador2 in jornada:
                assert jugador1 != jugador2
