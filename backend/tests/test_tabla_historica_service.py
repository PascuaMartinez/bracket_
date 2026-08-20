"""Pruebas del acumulado histórico."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from services import tabla_historica_service as historica


def torneo(id, nombre, fecha, estado="finalizado"):
    return SimpleNamespace(id=id, nombre=nombre, fecha=fecha, estado=estado)


def fila(jugador_id, nombre, puesto, pj=0, pg=0, pp=0):
    return {"jugador_id": jugador_id, "nombre": nombre, "puesto": puesto,
            "pj": pj, "pg": pg, "pp": pp}


def calcular(torneos, tablas_por_torneo):
    with patch.object(historica.torneo_repository, "obtener_todos", return_value=torneos), \
         patch.object(historica.tabla_service, "calcular_tabla",
                      side_effect=lambda tid: tablas_por_torneo[tid]):
        return historica.calcular_tabla_historica()


def test_suma_los_puntos_de_cada_torneo():
    torneos = [torneo(1, "Enero", date(2026, 1, 1)), torneo(2, "Marzo", date(2026, 3, 1))]
    tablas = {
        1: [fila(1, "Ana", puesto=1, pj=2, pg=2)],
        2: [fila(1, "Ana", puesto=3, pj=2, pg=1, pp=1)],
    }

    tabla = calcular(torneos, tablas)

    # 8 por salir primero + 6 por salir tercero
    assert tabla[0]["puntos"] == 14
    assert tabla[0]["torneos_jugados"] == 2


def test_del_sexto_en_adelante_todos_suman_un_punto():
    """Presentarse cuenta: el punto de participación premia la constancia."""
    assert historica.puntos_de_puesto(6) == 1
    assert historica.puntos_de_puesto(12) == 1


def test_la_escala_de_puntos_no_es_lineal():
    """La diferencia entre los primeros puestos pesa más que entre los
    últimos, que es como se siente ganar un torneo."""
    diferencia_arriba = historica.puntos_de_puesto(1) - historica.puntos_de_puesto(2)
    diferencia_abajo = historica.puntos_de_puesto(4) - historica.puntos_de_puesto(5)

    assert diferencia_arriba < diferencia_abajo


def test_no_cuenta_los_torneos_sin_finalizar():
    """Un torneo a medio jugar todavía no repartió nada."""
    torneos = [
        torneo(1, "Enero", date(2026, 1, 1)),
        torneo(2, "En curso", date(2026, 3, 1), estado="en_curso"),
    ]
    tablas = {1: [fila(1, "Ana", puesto=1)], 2: [fila(1, "Ana", puesto=1)]}

    tabla = calcular(torneos, tablas)

    assert tabla[0]["torneos_jugados"] == 1
    assert len(tabla[0]["insignias"]) == 1


def test_las_insignias_van_en_orden_cronologico():
    """Se leen como una línea de tiempo, así que el orden importa aunque
    los torneos vengan del repositorio de más nuevo a más viejo."""
    torneos = [
        torneo(2, "Marzo", date(2026, 3, 1)),
        torneo(1, "Enero", date(2026, 1, 1)),
    ]
    tablas = {1: [fila(1, "Ana", puesto=1)], 2: [fila(1, "Ana", puesto=2)]}

    tabla = calcular(torneos, tablas)

    nombres = [i["torneo_nombre"] for i in tabla[0]["insignias"]]
    assert nombres == ["Enero", "Marzo"]


def test_desempata_por_puntos_de_victoria():
    """Dos que sumaron lo mismo por puesto se separan por partidos
    ganados."""
    torneos = [torneo(1, "Enero", date(2026, 1, 1))]
    tablas = {1: [
        fila(1, "Ana", puesto=1, pj=5, pg=5),
        fila(2, "Beto", puesto=1, pj=5, pg=3, pp=2),
    ]}

    tabla = calcular(torneos, tablas)

    assert tabla[0]["nombre"] == "Ana"
    assert tabla[0]["puesto"] == 1
    assert tabla[1]["puesto"] == 2


def test_comparten_puesto_solo_si_empatan_en_todo():
    torneos = [torneo(1, "Enero", date(2026, 1, 1))]
    tablas = {1: [
        fila(1, "Ana", puesto=1, pj=4, pg=3, pp=1),
        fila(2, "Beto", puesto=1, pj=4, pg=3, pp=1),
    ]}

    tabla = calcular(torneos, tablas)

    assert tabla[0]["puesto"] == tabla[1]["puesto"] == 1


def test_sin_torneos_devuelve_tabla_vacia():
    assert calcular([], {}) == []
