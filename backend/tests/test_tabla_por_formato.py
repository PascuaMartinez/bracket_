"""
Pruebas de que cada formato ordena su tabla con su propio criterio.

Lo que importa acá no es solo que cada uno calcule bien, sino que los
tres devuelvan la MISMA FORMA de resultado: es lo que permite que el
acumulado histórico los trate igual sin saber de qué formato vienen.
"""
from types import SimpleNamespace
from unittest.mock import patch

from services import tabla_service


CAMPOS_QUE_TODA_TABLA_DEBE_TRAER = ("jugador_id", "nombre", "puesto", "pj", "pg", "pp", "win_rate")


def participante(jugador_id, nombre):
    return {"jugador_id": jugador_id, "nombre": nombre, "torneo_jugador_id": jugador_id}


def partido(jugador1, jugador2, ganador, ronda=None, orden=1, es_pase_libre=False, es_desempate=False):
    return SimpleNamespace(
        jugador1_id=jugador1, jugador2_id=jugador2, ganador_id=ganador,
        ronda=ronda, orden=orden, estado="finalizado", es_pase_libre=es_pase_libre, es_desempate=es_desempate,
    )


def calcular_eliminacion(participantes, partidos):
    torneo = SimpleNamespace(id=1, modo="eliminacion")
    with patch.object(tabla_service.torneo_repository, "obtener_por_id", return_value=torneo), \
         patch.object(tabla_service.torneo_repository, "obtener_participantes",
                      return_value=participantes), \
         patch.object(tabla_service.partido_repository, "obtener_por_torneo",
                      return_value=partidos):
        return tabla_service.calcular_tabla(1)


def calcular_rey(estado, partidos):
    torneo = SimpleNamespace(id=1, modo="rey_de_la_cancha")
    with patch.object(tabla_service.torneo_repository, "obtener_por_id", return_value=torneo), \
         patch.object(tabla_service.vidas_repository, "obtener_estado", return_value=estado), \
         patch.object(tabla_service.partido_repository, "obtener_por_torneo",
                      return_value=partidos):
        return tabla_service.calcular_tabla(1)


def test_eliminacion_ordena_por_hasta_donde_llego_cada_uno():
    """No por partidos ganados: en un cuadro, llegar a la final vale más
    que haber ganado muchos partidos en rondas tempranas."""
    participantes = [participante(i, f"J{i}") for i in range(1, 5)]
    partidos = [
        partido(1, 2, ganador=1, ronda=1, orden=1),
        partido(3, 4, ganador=3, ronda=1, orden=2),
        partido(1, 3, ganador=1, ronda=2, orden=3),   # final
    ]

    tabla = calcular_eliminacion(participantes, partidos)

    assert tabla[0]["nombre"] == "J1"   # campeón
    assert tabla[1]["nombre"] == "J3"   # finalista


def test_eliminacion_los_que_caen_en_la_misma_ronda_comparten_puesto():
    """El cuadro nunca los enfrentó: decidir cuál fue mejor sería inventar
    una comparación que el torneo no hizo."""
    participantes = [participante(i, f"J{i}") for i in range(1, 5)]
    partidos = [
        partido(1, 2, ganador=1, ronda=1, orden=1),
        partido(3, 4, ganador=3, ronda=1, orden=2),
        partido(1, 3, ganador=1, ronda=2, orden=3),
    ]

    tabla = calcular_eliminacion(participantes, partidos)

    eliminados_en_primera = [f for f in tabla if f["nombre"] in ("J2", "J4")]
    assert eliminados_en_primera[0]["puesto"] == eliminados_en_primera[1]["puesto"]


def test_eliminacion_los_pases_libres_no_cuentan_como_partido():
    participantes = [participante(i, f"J{i}") for i in range(1, 4)]
    partidos = [
        partido(1, None, ganador=1, ronda=1, orden=1, es_pase_libre=True),
        partido(2, 3, ganador=2, ronda=1, orden=2),
        partido(1, 2, ganador=1, ronda=2, orden=3),
    ]

    tabla = calcular_eliminacion(participantes, partidos)

    campeon = next(f for f in tabla if f["nombre"] == "J1")
    assert campeon["pj"] == 1   # solo la final


def test_rey_de_la_cancha_usa_su_propia_formula():
    estado = [
        {"jugador_id": 1, "nombre": "Ana", "eliminado": False, "orden_eliminacion": None},
        {"jugador_id": 2, "nombre": "Beto", "eliminado": True, "orden_eliminacion": 2},
        {"jugador_id": 3, "nombre": "Caro", "eliminado": True, "orden_eliminacion": 1},
    ]
    partidos = [
        partido(1, 2, ganador=1, orden=1),
        partido(1, 3, ganador=1, orden=2),
        partido(1, 2, ganador=1, orden=3),
    ]

    tabla = calcular_rey(estado, partidos)

    assert tabla[0]["nombre"] == "Ana"   # el campeón, siempre primero
    assert tabla[0]["puesto"] == 1


def test_los_tres_formatos_devuelven_la_misma_forma():
    """Es lo que permite que el acumulado histórico los sume sin saber de
    qué formato vienen."""
    participantes = [participante(i, f"J{i}") for i in range(1, 4)]
    partidos_elim = [
        partido(1, 2, ganador=1, ronda=1, orden=1),
        partido(1, 3, ganador=1, ronda=2, orden=2),
    ]
    estado_rey = [
        {"jugador_id": 1, "nombre": "Ana", "eliminado": False, "orden_eliminacion": None},
        {"jugador_id": 2, "nombre": "Beto", "eliminado": True, "orden_eliminacion": 1},
    ]

    tablas = [
        calcular_eliminacion(participantes, partidos_elim),
        calcular_rey(estado_rey, [partido(1, 2, ganador=1, orden=1)]),
    ]

    for tabla in tablas:
        assert tabla, "ninguna tabla debería salir vacía"
        for fila in tabla:
            for campo in CAMPOS_QUE_TODA_TABLA_DEBE_TRAER:
                assert campo in fila, f"falta {campo}"
