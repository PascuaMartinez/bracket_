"""Pruebas de las estadísticas de un jugador."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from services import estadisticas_service


def partido(torneo_id, jugador1, jugador2, ganador, orden=1, es_pase_libre=False,
            rondas=None):
    return SimpleNamespace(
        torneo_id=torneo_id, jugador1_id=jugador1, jugador2_id=jugador2,
        ganador_id=ganador, orden=orden, estado="finalizado",
        es_pase_libre=es_pase_libre, rondas_jugadas=rondas,
    )


def calcular(partidos, jugador_id=1, nombres=None):
    nombres = nombres or {1: "Ana", 2: "Beto", 3: "Caro"}
    jugadores = [SimpleNamespace(id=i, nombre=n) for i, n in nombres.items()]
    torneos = [
        SimpleNamespace(id=1, estado="finalizado", nombre="Enero",
                        fecha=date(2026, 1, 1)),
        SimpleNamespace(id=2, estado="finalizado", nombre="Marzo",
                        fecha=date(2026, 3, 1)),
    ]

    with patch.object(estadisticas_service.jugador_repository, "obtener_por_id",
                      return_value=SimpleNamespace(id=jugador_id, nombre=nombres[jugador_id])), \
         patch.object(estadisticas_service.jugador_repository, "obtener_todos",
                      return_value=jugadores), \
         patch.object(estadisticas_service.torneo_repository, "obtener_todos",
                      return_value=torneos), \
         patch.object(estadisticas_service.partido_repository, "obtener_por_torneo",
                      side_effect=lambda tid: [p for p in partidos if p.torneo_id == tid]), \
         patch("services.tabla_service.calcular_tabla",
               return_value=[{"jugador_id": jugador_id, "puesto": 1}]):
        return estadisticas_service.obtener_estadisticas(jugador_id)


def test_cuenta_el_record():
    stats = calcular([
        partido(1, 1, 2, ganador=1),
        partido(1, 1, 3, ganador=1),
        partido(1, 1, 2, ganador=2),
    ])

    assert stats["partidos_jugados"] == 3
    assert stats["partidos_ganados"] == 2
    assert stats["partidos_perdidos"] == 1


def test_devuelve_todos_los_que_empatan_en_el_maximo():
    """Si jugó lo mismo contra dos rivales, las dos respuestas son igual
    de ciertas: elegir una sería inventar un desempate."""
    stats = calcular([
        partido(1, 1, 2, ganador=1),
        partido(1, 1, 3, ganador=1),
    ])

    assert len(stats["rival_mas_frecuente"]) == 2


def test_no_devuelve_nada_cuando_el_maximo_es_cero():
    """'Contra quién perdió más' no debería listar a todos los rivales
    cuando el jugador nunca perdió."""
    stats = calcular([
        partido(1, 1, 2, ganador=1),
        partido(1, 1, 3, ganador=1),
    ])

    assert stats["contra_quien_perdio_mas"] == []


def test_los_pases_libres_no_cuentan_como_victoria():
    """No se jugaron: contarlos inflaría el récord de quien tuvo la suerte
    de que el cuadro no cerrara justo."""
    stats = calcular([
        partido(1, 1, 2, ganador=1),
        partido(1, 1, None, ganador=1, es_pase_libre=True),
    ])

    assert stats["partidos_jugados"] == 1


def test_mejor_racha():
    stats = calcular([
        partido(1, 1, 2, ganador=1, orden=1),
        partido(1, 1, 3, ganador=1, orden=2),
        partido(1, 1, 2, ganador=2, orden=3),   # corta la racha
        partido(1, 1, 3, ganador=1, orden=4),
    ])

    assert stats["mejor_racha"] == 2


def test_la_racha_respeta_el_orden_cronologico():
    """Los partidos pueden venir en cualquier orden del repositorio; la
    racha tiene que calcularse sobre el orden en que se jugaron."""
    stats = calcular([
        partido(1, 1, 3, ganador=1, orden=4),
        partido(1, 1, 2, ganador=2, orden=3),
        partido(1, 1, 3, ganador=1, orden=2),
        partido(1, 1, 2, ganador=1, orden=1),
    ])

    assert stats["mejor_racha"] == 2


def test_cuenta_torneos_distintos():
    stats = calcular([
        partido(1, 1, 2, ganador=1),
        partido(1, 1, 3, ganador=1),
        partido(2, 1, 2, ganador=1),
    ])

    assert stats["torneos_jugados"] == 2


def test_sin_partidos_no_falla():
    """El caso que rompería con una división por cero."""
    stats = calcular([])

    assert stats["partidos_jugados"] == 0
    assert stats["win_rate"] == 0
    assert stats["mejor_racha"] == 0
    assert stats["rival_mas_frecuente"] == []
