"""
Pruebas de ocultar y borrar jugadores.

La regla de fondo: un torneo es un hecho que ocurrió, así que sacar a un
participante no puede dejar partidos con un solo jugador.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import jugador_service


def preparar(tiene_partidos, en_torneo_abierto=False, existe=True):
    return (
        patch.object(jugador_service.jugador_repository, "obtener_por_id",
                     return_value=SimpleNamespace(id=1) if existe else None),
        patch.object(jugador_service.jugador_repository, "tiene_partidos",
                     return_value=tiene_partidos),
        patch.object(jugador_service.jugador_repository, "esta_en_torneo_sin_terminar",
                     return_value=en_torneo_abierto),
    )


def test_un_jugador_sin_partidos_se_borra_de_verdad():
    """No hay historia que preservar, y dejarlo oculto sería juntar
    basura."""
    with preparar(tiene_partidos=False)[0], preparar(False)[1], preparar(False)[2], \
         patch.object(jugador_service.jugador_repository, "eliminar") as eliminar, \
         patch.object(jugador_service.jugador_repository, "cambiar_visibilidad") as ocultar:
        resultado = jugador_service.eliminar_jugador(1)

    assert resultado == "eliminado"
    eliminar.assert_called_once()
    ocultar.assert_not_called()


def test_un_jugador_con_partidos_se_oculta():
    """Borrarlo dejaría partidos con un solo participante: la final de
    enero la jugaron dos personas, aunque una después se haya ido."""
    with preparar(tiene_partidos=True)[0], preparar(True)[1], preparar(True)[2], \
         patch.object(jugador_service.jugador_repository, "eliminar") as eliminar, \
         patch.object(jugador_service.jugador_repository, "cambiar_visibilidad") as ocultar:
        resultado = jugador_service.eliminar_jugador(1)

    assert resultado == "ocultado"
    ocultar.assert_called_once_with(1, True)
    eliminar.assert_not_called()


def test_no_se_puede_sacar_a_alguien_de_un_torneo_en_curso():
    """Dejaría la pantalla de cargar resultado mostrando un partido contra
    un fantasma."""
    with preparar(True, en_torneo_abierto=True)[0], \
         preparar(True, en_torneo_abierto=True)[1], \
         preparar(True, en_torneo_abierto=True)[2]:
        with pytest.raises(jugador_service.JugadorInvalidoError, match="sin terminar"):
            jugador_service.eliminar_jugador(1)


def test_sacar_a_alguien_que_no_existe_falla():
    with preparar(False, existe=False)[0], preparar(False)[1], preparar(False)[2]:
        with pytest.raises(jugador_service.JugadorNoEncontradoError):
            jugador_service.eliminar_jugador(99)


def test_mostrar_devuelve_al_jugador_al_sistema():
    with patch.object(jugador_service.jugador_repository, "cambiar_visibilidad",
                      return_value=True) as cambiar:
        jugador_service.mostrar_jugador(1)

    cambiar.assert_called_once_with(1, False)


def test_los_ocultos_no_aparecen_por_defecto():
    with patch.object(jugador_service.jugador_repository, "obtener_todos",
                      return_value=[]) as obtener:
        jugador_service.listar_jugadores()

    assert obtener.call_args[0][0] is False
