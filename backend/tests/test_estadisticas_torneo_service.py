"""Pruebas de las estadísticas de un torneo."""
from types import SimpleNamespace
from unittest.mock import patch

from services import estadisticas_torneo_service as est


def partido(jugador1, jugador2, ganador, orden=1, rondas=None, es_pase_libre=False, es_desempate=False):
    return SimpleNamespace(
        jugador1_id=jugador1, jugador2_id=jugador2, ganador_id=ganador,
        orden=orden, rondas_jugadas=rondas, estado="finalizado",
        es_pase_libre=es_pase_libre, es_desempate=es_desempate,
    )


def calcular(partidos, cantidad_jugadores=3):
    nombres = {1: "Ana", 2: "Beto", 3: "Caro"}
    with patch.object(est.torneo_repository, "obtener_por_id",
                      return_value=SimpleNamespace(id=1)), \
         patch.object(est.partido_repository, "obtener_por_torneo",
                      return_value=partidos), \
         patch.object(est.jugador_repository, "obtener_todos",
                      return_value=[SimpleNamespace(id=i, nombre=n)
                                    for i, n in nombres.items()]), \
         patch.object(est.torneo_repository, "obtener_participantes",
                      return_value=[{"jugador_id": i} for i in range(1, cantidad_jugadores + 1)]):
        return est.obtener_estadisticas(1)


def test_cuenta_barridas_y_cerrados():
    stats = calcular([
        partido(1, 2, ganador=1, rondas=2),
        partido(1, 3, ganador=1, rondas=3),
        partido(2, 3, ganador=2, rondas=2),
    ])

    assert stats["barridas"] == 2
    assert stats["cerrados"] == 1


def test_informa_cuantos_partidos_tienen_el_dato_de_rondas():
    """Sin eso, '2 barridas' no dice nada: puede ser 2 de 3 o 2 de 40."""
    stats = calcular([
        partido(1, 2, ganador=1, rondas=2),
        partido(1, 3, ganador=1),   # sin registrar
    ])

    assert stats["partidos_con_rondas"] == 1
    assert stats["partidos_jugados"] == 2


def test_los_pases_libres_no_cuentan_como_partidos():
    stats = calcular([
        partido(1, 2, ganador=1),
        partido(3, None, ganador=3, es_pase_libre=True),
    ])

    assert stats["partidos_jugados"] == 1


def test_detecta_la_mejor_racha_del_torneo():
    stats = calcular([
        partido(1, 2, ganador=1, orden=1),
        partido(1, 3, ganador=1, orden=2),
        partido(1, 2, ganador=2, orden=3),   # se corta
    ])

    assert stats["mejor_racha"][0]["nombre"] == "Ana"
    assert stats["mejor_racha"][0]["veces"] == 2


def test_una_sola_victoria_no_es_una_racha():
    """La tendrían todos los que ganaron algún partido: no dice nada."""
    stats = calcular([partido(1, 2, ganador=1), partido(2, 3, ganador=2)])

    assert stats["mejor_racha"] == []


def test_devuelve_todos_los_que_empatan_en_el_maximo():
    stats = calcular([
        partido(1, 2, ganador=1, orden=1),
        partido(1, 3, ganador=1, orden=2),
        partido(2, 3, ganador=2, orden=3),
        partido(2, 3, ganador=2, orden=4),
    ])

    assert len(stats["mejor_racha"]) == 2


def test_sin_partidos_no_falla():
    stats = calcular([])

    assert stats["partidos_jugados"] == 0
    assert stats["mas_victorias"] == []
    assert stats["mejor_racha"] == []
