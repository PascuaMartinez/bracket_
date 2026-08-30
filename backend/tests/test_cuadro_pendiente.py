"""
Pruebas de la espera antes de sembrar el cuadro.

Lo que se protege: que el cuadro no arranque solo, y que la decisión de
cómo sembrarlo solo esté disponible cuando corresponde.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import partido_service


def torneo(modo="grupos_eliminacion"):
    return SimpleNamespace(id=1, modo=modo)


def test_no_hay_cuadro_pendiente_si_falta_resolver_un_empate():
    with patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo()), \
         patch.object(partido_service.grupo_repository, "hay_indecisos",
                      return_value=True):
        assert not partido_service.cuadro_pendiente(1)


def test_hay_cuadro_pendiente_cuando_los_grupos_terminaron():
    with patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo()), \
         patch.object(partido_service.grupo_repository, "hay_indecisos",
                      return_value=False), \
         patch.object(partido_service.grupo_repository, "obtener_clasificados",
                      return_value=[{"jugador_id": 1}, {"jugador_id": 2}]), \
         patch.object(partido_service.partido_repository, "obtener_por_torneo",
                      return_value=[]):
        assert partido_service.cuadro_pendiente(1)


def test_no_esta_pendiente_si_el_cuadro_ya_se_armo():
    con_cuadro = SimpleNamespace(ronda=1)
    with patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo()), \
         patch.object(partido_service.grupo_repository, "hay_indecisos",
                      return_value=False), \
         patch.object(partido_service.grupo_repository, "obtener_clasificados",
                      return_value=[{"jugador_id": 1}, {"jugador_id": 2}]), \
         patch.object(partido_service.partido_repository, "obtener_por_torneo",
                      return_value=[con_cuadro]):
        assert not partido_service.cuadro_pendiente(1)


def test_otros_formatos_nunca_tienen_cuadro_pendiente():
    """Solo grupos + eliminación pasa por esta espera."""
    with patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo(modo="eliminacion")):
        assert not partido_service.cuadro_pendiente(1)


def test_sembrar_falla_si_el_cuadro_no_esta_pendiente():
    with patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo()), \
         patch.object(partido_service, "cuadro_pendiente", return_value=False):
        with pytest.raises(partido_service.ResultadoInvalidoError, match="ya está armado"):
            partido_service.sembrar_cuadro_manual(1)


def test_sembrar_manual_rechaza_un_orden_que_no_son_los_clasificados():
    with patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo()), \
         patch.object(partido_service, "cuadro_pendiente", return_value=True), \
         patch.object(partido_service.grupo_repository, "obtener_clasificados",
                      return_value=[{"jugador_id": 1}, {"jugador_id": 2}]):
        with pytest.raises(partido_service.ResultadoInvalidoError, match="clasificados"):
            partido_service.sembrar_cuadro_manual(1, [1, 2, 99])
