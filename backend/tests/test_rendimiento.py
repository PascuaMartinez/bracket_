"""
Pruebas de rendimiento.

No miden tiempo -- depende de la máquina -- sino la cantidad de consultas,
que es una propiedad del código. Lo que protegen es que las operaciones
que recorren muchos torneos no vuelvan a consultar de a uno: es un error
fácil de reintroducir sin notarlo, porque el código sigue funcionando y
solo se pone lento a medida que se acumulan torneos.
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import cache
from services import tabla_historica_service as historica
from services import tabla_service


def escenario(cantidad_torneos, cantidad_jugadores=8):
    torneos = [
        SimpleNamespace(id=i, nombre=f"T{i}", fecha=date(2026, 1, 1),
                        estado="finalizado", modo="todos_contra_todos")
        for i in range(1, cantidad_torneos + 1)
    ]
    participantes = [
        {"jugador_id": j, "nombre": f"J{j}", "torneo_jugador_id": j}
        for j in range(1, cantidad_jugadores + 1)
    ]
    partidos = [
        SimpleNamespace(jugador1_id=a, jugador2_id=b, ganador_id=a,
                        estado="finalizado", ronda=None, es_pase_libre=False, orden=1)
        for a in range(1, cantidad_jugadores + 1)
        for b in range(a + 1, cantidad_jugadores + 1)
    ]
    return torneos, participantes, partidos


def contar_consultas(cantidad_torneos):
    # El cache se limpia antes de medir: con algo guardado no se
    # consultaría nada, y la medición diría cero sin que eso signifique
    # que el código consulta poco.
    cache.invalidar_todo()

    torneos, participantes, partidos = escenario(cantidad_torneos)
    consultas = []

    def registrar(valor):
        def responder(*args, **kwargs):
            consultas.append(1)
            return valor
        return responder

    with patch.object(historica.torneo_repository, "obtener_todos",
                      side_effect=registrar(torneos)), \
         patch.object(historica.torneo_repository, "obtener_participantes_de_varios",
                      side_effect=registrar({t.id: participantes for t in torneos})), \
         patch.object(historica.partido_repository, "obtener_de_varios_torneos",
                      side_effect=registrar({t.id: partidos for t in torneos})), \
         patch.object(tabla_service.torneo_repository, "obtener_por_id",
                      side_effect=registrar(torneos[0] if torneos else None)), \
         patch.object(tabla_service.torneo_repository, "obtener_participantes",
                      side_effect=registrar(participantes)), \
         patch.object(tabla_service.partido_repository, "obtener_por_torneo",
                      side_effect=registrar(partidos)):
        historica.calcular_tabla_historica()

    return len(consultas)


def test_la_tabla_historica_no_consulta_de_a_un_torneo():
    """Con tres consultas por torneo, 50 torneos serían 151 idas a la
    base. Traer todo junto lo deja en una cantidad fija."""
    assert contar_consultas(cantidad_torneos=20) <= 5


@pytest.mark.parametrize("cantidad_torneos", [5, 10, 20, 50])
def test_la_cantidad_de_consultas_no_crece_con_los_torneos(cantidad_torneos):
    """Esta es la propiedad que importa: que agregar torneos no encarezca
    la consulta. Si alguien vuelve a pedir los datos torneo por torneo,
    este test lo detecta antes de que se note en producción."""
    assert contar_consultas(cantidad_torneos) == contar_consultas(5)
