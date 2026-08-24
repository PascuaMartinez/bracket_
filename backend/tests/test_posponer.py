"""Pruebas de posponer y retomar partidos."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import partido_service


def partido(estado="pendiente"):
    return SimpleNamespace(id=1, torneo_id=1, jugador1_id=1, jugador2_id=2,
                           estado=estado, ronda=None, orden=1)


def test_posponer_cambia_el_estado():
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=partido()), \
         patch.object(partido_service.partido_repository, "cambiar_estado") as cambiar:
        partido_service.posponer(1)

    cambiar.assert_called_once_with(1, "pospuesto")


def test_no_se_puede_posponer_un_partido_ya_jugado():
    """Posponer algo que ya pasó no significa nada, y dejaría un resultado
    cargado en un estado que dice que no se jugó."""
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=partido(estado="finalizado")):
        with pytest.raises(partido_service.ResultadoInvalidoError):
            partido_service.posponer(1)


def test_posponer_uno_que_no_existe_falla():
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=None):
        with pytest.raises(partido_service.PartidoNoEncontradoError):
            partido_service.posponer(99)


def test_retomar_lo_devuelve_a_pendiente():
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=partido(estado="pospuesto")), \
         patch.object(partido_service.partido_repository, "cambiar_estado") as cambiar:
        partido_service.retomar(1)

    cambiar.assert_called_once_with(1, "pendiente")


def test_no_se_puede_retomar_uno_que_no_estaba_pospuesto():
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=partido(estado="pendiente")):
        with pytest.raises(partido_service.ResultadoInvalidoError):
            partido_service.retomar(1)
