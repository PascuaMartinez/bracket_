"""
Pruebas del rating Bradley-Terry.

Se prueban las propiedades del modelo, no valores concretos: si mañana se
ajusta la escala o el suavizado, lo que tiene que seguir siendo cierto es
que ganarle a los fuertes valga más que ganarle a los flojos.
"""
import pytest

from services.rating_service import RATING_BASE, calcular_ratings, probabilidad


def test_el_orden_refleja_la_jerarquia():
    partidos = []
    for mejor in range(1, 5):
        for peor in range(mejor + 1, 5):
            partidos += [(mejor, peor)] * 3

    ratings = calcular_ratings([1, 2, 3, 4], partidos)

    assert ratings[1] > ratings[2] > ratings[3] > ratings[4]


def test_ganarle_a_los_fuertes_vale_mas_que_ganarle_a_los_flojos():
    """Es lo que el win rate no distingue, y la razón de usar este
    modelo."""
    # 1 y 3 tienen el mismo récord (50%), pero contra rivales distintos.
    partidos = (
        [(1, 2)] * 10 + [(2, 1)] * 10      # 1 empareja con el fuerte
        + [(3, 4)] * 10 + [(4, 3)] * 10    # 3 empareja con el débil
        + [(2, 4)] * 10                     # el fuerte le gana al débil
    )

    ratings = calcular_ratings([1, 2, 3, 4], partidos)

    assert ratings[1] > ratings[3]


def test_un_invicto_no_rompe_el_calculo():
    """Sin suavizado, el modelo no puede explicar 'nunca perdió' con un
    número finito y la fuerza se dispara al infinito."""
    ratings = calcular_ratings([1, 2, 3], [(1, 2), (1, 3), (1, 2), (1, 3)])

    assert all(isinstance(r, int) for r in ratings.values())
    assert ratings[1] > ratings[2]


def test_el_que_perdio_todo_tampoco():
    ratings = calcular_ratings([1, 2], [(1, 2)] * 5)

    assert ratings[2] < ratings[1]
    assert ratings[2] > 0


def test_sin_partidos_todos_quedan_en_la_base():
    """Sin datos no hay nada que estimar, y dejarlos afuera los haría
    desaparecer de la tabla."""
    ratings = calcular_ratings([1, 2, 3], [])

    assert all(r == RATING_BASE for r in ratings.values())


def test_con_un_solo_jugador_no_falla():
    assert calcular_ratings([1], []) == {1: RATING_BASE}


def test_sin_jugadores_devuelve_vacio():
    assert calcular_ratings([], []) == {}


def test_dos_jugadores_parejos_quedan_parejos():
    ratings = calcular_ratings([1, 2], [(1, 2)] * 10 + [(2, 1)] * 10)

    assert abs(ratings[1] - ratings[2]) <= 1


def test_mismo_rating_es_mitad_y_mitad():
    assert probabilidad(1000, 1000) == pytest.approx(0.5)


def test_mas_rating_da_mas_probabilidad():
    assert probabilidad(1200, 1000) > 0.5
    assert probabilidad(1000, 1200) < 0.5


def test_las_dos_probabilidades_suman_uno():
    """Alguno de los dos gana: no hay empates en este dominio."""
    assert probabilidad(1150, 900) + probabilidad(900, 1150) == pytest.approx(1.0)


def test_solo_importa_la_diferencia_de_rating():
    """Dos jugadores separados por 200 puntos tienen la misma
    probabilidad, sin importar si son 1000 y 1200 o 1800 y 2000."""
    assert probabilidad(1200, 1000) == pytest.approx(probabilidad(2000, 1800))
