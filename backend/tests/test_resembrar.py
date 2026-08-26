"""
Pruebas del reordenamiento del cuadro.

Lo que se protege: que no se puedan descartar resultados reales, y que el
orden nuevo no cambie quiénes participan.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import partido_service


def partido(estado="pendiente", es_pase_libre=False):
    return SimpleNamespace(id=1, estado=estado, es_pase_libre=es_pase_libre)


def test_se_puede_reordenar_antes_de_jugar():
    with patch.object(partido_service.partido_repository, "obtener_por_ronda",
                      return_value=[partido(), partido()]):
        permitido, _ = partido_service.puede_resembrarse(1)

    assert permitido


def test_no_se_puede_si_ya_se_jugo_algo():
    """Reordenar después significaría descartar resultados reales para
    reemplazarlos por partidos que nunca ocurrieron."""
    with patch.object(partido_service.partido_repository, "obtener_por_ronda",
                      return_value=[partido(estado="finalizado"), partido()]):
        permitido, motivo = partido_service.puede_resembrarse(1)

    assert not permitido
    assert "Ya se jugó" in motivo


def test_los_pases_libres_no_cuentan_como_jugados():
    """No se jugaron, y son justamente parte de lo que se quiere poder
    reacomodar."""
    with patch.object(partido_service.partido_repository, "obtener_por_ronda",
                      return_value=[partido(estado="finalizado", es_pase_libre=True),
                                    partido()]):
        permitido, _ = partido_service.puede_resembrarse(1)

    assert permitido


def test_sin_cuadro_no_hay_nada_que_reordenar():
    with patch.object(partido_service.partido_repository, "obtener_por_ronda",
                      return_value=[]):
        permitido, motivo = partido_service.puede_resembrarse(1)

    assert not permitido
    assert "no tiene un cuadro" in motivo


def preparar_resembrado(inscriptos):
    return (
        patch.object(partido_service.partido_repository, "obtener_por_ronda",
                     return_value=[partido(), partido()]),
        patch.object(partido_service.torneo_repository, "obtener_participantes",
                     return_value=[{"jugador_id": j} for j in inscriptos]),
    )


def test_rechaza_un_orden_al_que_le_falta_alguien():
    """Quedaría fuera del torneo sin que nadie lo haya decidido."""
    ronda, participantes = preparar_resembrado([1, 2, 3, 4])
    with ronda, participantes:
        with pytest.raises(partido_service.ResultadoInvalidoError, match="mismos"):
            partido_service.resembrar(1, [1, 2, 3])


def test_rechaza_un_orden_con_alguien_de_mas():
    """Entraría al torneo alguien que no se anotó."""
    ronda, participantes = preparar_resembrado([1, 2, 3, 4])
    with ronda, participantes:
        with pytest.raises(partido_service.ResultadoInvalidoError, match="mismos"):
            partido_service.resembrar(1, [1, 2, 3, 4, 5])


def test_acepta_los_mismos_en_otro_orden():
    ronda, participantes = preparar_resembrado([1, 2, 3, 4])
    with ronda, participantes, \
         patch.object(partido_service.partido_repository, "eliminar_ronda"), \
         patch.object(partido_service.partido_repository, "obtener_max_orden",
                      return_value=0), \
         patch.object(partido_service.partido_repository, "crear_muchos") as crear:
        cantidad = partido_service.resembrar(1, [4, 3, 2, 1])

    assert cantidad == 2
    creados = crear.call_args[0][0]
    # El primero de la lista nueva se enfrenta al último, como en cualquier
    # siembra.
    assert creados[0]["jugador1_id"] == 4
    assert creados[0]["jugador2_id"] == 1
