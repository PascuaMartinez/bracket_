"""Pruebas del armado de la fase de grupos."""
import pytest

from services.grupos_service import (
    nombre_de_grupo, repartir_cupos, repartir_en_grupos,
)


@pytest.mark.parametrize("cantidad_jugadores,cantidad_grupos", [
    (8, 2), (9, 2), (12, 3), (10, 4), (6, 3), (7, 2),
])
def test_no_se_pierde_ni_se_duplica_nadie(cantidad_jugadores, cantidad_grupos):
    jugadores = list(range(1, cantidad_jugadores + 1))

    grupos = repartir_en_grupos(jugadores, cantidad_grupos)

    repartidos = [j for grupo in grupos for j in grupo]
    assert sorted(repartidos) == jugadores


@pytest.mark.parametrize("cantidad_jugadores,cantidad_grupos", [
    (8, 2), (9, 2), (12, 3), (10, 4), (7, 3),
])
def test_los_grupos_quedan_parejos(cantidad_jugadores, cantidad_grupos):
    """A lo sumo uno de diferencia: si un grupo tuviera dos más que otro,
    clasificar sería notoriamente más difícil ahí."""
    grupos = repartir_en_grupos(list(range(1, cantidad_jugadores + 1)), cantidad_grupos)

    tamanos = [len(g) for g in grupos]
    assert max(tamanos) - min(tamanos) <= 1


def test_los_mejores_quedan_repartidos_y_no_juntos():
    """Con reparto por bloques, los primeros de la lista caerían todos en
    el mismo grupo y se eliminarían entre sí gente que en otro grupo
    hubiera clasificado."""
    grupos = repartir_en_grupos([1, 2, 3, 4, 5, 6, 7, 8], cantidad_grupos=2)

    grupo_del_uno = next(i for i, g in enumerate(grupos) if 1 in g)
    grupo_del_dos = next(i for i, g in enumerate(grupos) if 2 in g)
    assert grupo_del_uno != grupo_del_dos


def test_reparto_de_cupos_parejo():
    assert repartir_cupos(4, [4, 4]) == [2, 2]


def test_el_cupo_sobrante_va_al_grupo_mas_grande():
    """En un grupo de 5 clasificar es más difícil que en uno de 4: hay más
    rivales por el mismo lugar, así que el cupo extra corresponde ahí."""
    assert repartir_cupos(5, [5, 4]) == [3, 2]


def test_no_clasifican_mas_de_los_que_hay_en_el_grupo():
    """Si sobran cupos, se pierden en vez de inventar clasificados."""
    cupos = repartir_cupos(8, [3, 3])

    assert cupos == [3, 3]
    assert sum(cupos) == 6


def test_todos_los_cupos_se_reparten():
    for cupos_totales, tamanos in [(5, [4, 4]), (7, [4, 4, 4]), (3, [3, 3])]:
        assert sum(repartir_cupos(cupos_totales, tamanos)) == cupos_totales


def test_sin_grupos_no_falla():
    assert repartir_cupos(4, []) == []


@pytest.mark.parametrize("indice,nombre", [(0, "Grupo A"), (1, "Grupo B"), (25, "Grupo Z")])
def test_nombre_de_grupo(indice, nombre):
    assert nombre_de_grupo(indice) == nombre


def test_mas_alla_de_la_z_usa_numeros():
    """Combinar letras (AA, AB) sería más confuso que numerarlos."""
    assert nombre_de_grupo(26) == "Grupo 27"


def test_los_partidos_de_distintos_grupos_se_intercalan():
    """Si se jugaran todos los partidos del Grupo A antes de arrancar el
    Grupo B, ese grupo quedaría sin jugar nada hasta que el otro termine
    entero. Los grupos tienen que avanzar en paralelo."""
    from unittest.mock import patch

    from services import partido_service as ps

    capturados = []

    def capturar(lista, con_ronda=False):
        capturados.extend(lista)

    ids_de_grupo = iter([1, 2])
    with patch.object(ps.grupo_repository, "crear",
                      side_effect=lambda t, n: next(ids_de_grupo)), \
         patch.object(ps.grupo_repository, "asignar_jugadores"), \
         patch.object(ps.partido_repository, "crear_muchos", side_effect=capturar), \
         patch.object(ps.torneo_repository, "cambiar_estado"):
        ps._generar_grupos(1, [1, 2, 3, 4, 5, 6, 7, 8], cantidad_grupos=2)

    grupo_a = {1, 4, 5, 8}
    grupo_b = {2, 3, 6, 7}

    def grupo_de(partido):
        return "A" if partido["jugador1_id"] in grupo_a else "B"

    primeros_cuatro = [grupo_de(p) for p in capturados[:4]]
    assert set(primeros_cuatro) == {"A", "B"}, (
        "los primeros partidos generados deberían tocar a los dos grupos, "
        "no agotar uno antes de empezar el otro"
    )
