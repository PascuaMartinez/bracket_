"""Pruebas del armado del cuadro de eliminación."""
import pytest

from services.bracket_service import (
    cantidad_de_rondas, nombre_de_ronda, sembrar_primera_ronda,
)


@pytest.mark.parametrize("cantidad,rondas", [
    (2, 1), (3, 2), (4, 2), (5, 3), (8, 3), (9, 4), (16, 4),
])
def test_cantidad_de_rondas(cantidad, rondas):
    assert cantidad_de_rondas(cantidad) == rondas


@pytest.mark.parametrize("cantidad", [2, 3, 4, 5, 6, 7, 8, 9, 12, 16])
def test_todos_aparecen_exactamente_una_vez(cantidad):
    jugadores = list(range(1, cantidad + 1))

    cruces = sembrar_primera_ronda(jugadores)

    aparecen = [j for cruce in cruces for j in cruce if j is not None]
    assert sorted(aparecen) == jugadores


def test_los_mejores_sembrados_no_se_cruzan_de_entrada():
    """Si el 1 y el 2 se enfrentan en la primera ronda, uno queda afuera
    enseguida y el cuadro pierde interés."""
    cruces = sembrar_primera_ronda([1, 2, 3, 4, 5, 6, 7, 8])

    rivales_del_uno = [b for a, b in cruces if a == 1] + [a for a, b in cruces if b == 1]
    assert 2 not in rivales_del_uno


def test_el_primero_juega_contra_el_ultimo():
    cruces = sembrar_primera_ronda([1, 2, 3, 4])

    assert (1, 4) in cruces
    assert (2, 3) in cruces


def test_con_cantidad_que_no_es_potencia_de_dos_algunos_pasan_sin_jugar():
    """La alternativa -- hacer jugar una ronda previa solo a algunos --
    les daría un partido de desventaja frente al resto."""
    cruces = sembrar_primera_ronda([1, 2, 3, 4, 5, 6])

    pasan_sin_jugar = [a for a, b in cruces if b is None]
    assert len(pasan_sin_jugar) == 2


def test_los_que_pasan_sin_jugar_son_los_mejor_sembrados():
    """Es la ventaja que corresponde a haber quedado mejor ubicado."""
    cruces = sembrar_primera_ronda([1, 2, 3, 4, 5, 6])

    pasan_sin_jugar = [a for a, b in cruces if b is None]
    assert pasan_sin_jugar == [1, 2]


def test_con_potencia_de_dos_juegan_todos():
    for cantidad in (2, 4, 8, 16):
        cruces = sembrar_primera_ronda(list(range(1, cantidad + 1)))
        assert all(b is not None for a, b in cruces)


@pytest.mark.parametrize("partidos,nombre", [
    (1, "Final"), (2, "Semifinal"), (4, "Cuartos de final"), (8, "Octavos de final"),
])
def test_nombre_de_ronda(partidos, nombre):
    assert nombre_de_ronda(partidos) == nombre


def test_nombre_de_ronda_para_cuadros_grandes():
    """Sin nombre propio, se lo describe por su tamaño."""
    assert nombre_de_ronda(16) == "Ronda de 32"
