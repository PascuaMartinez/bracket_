"""
Pruebas de la corrección de resultados.

Lo que se protege es que corregir no rompa el torneo: en los formatos
donde un resultado define los partidos siguientes, cambiarlo tarde
dejaría el cuadro apuntando a alguien que ya no ganó.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import partido_service


def partido(estado="finalizado", ronda=None, orden=1):
    return SimpleNamespace(
        id=1, torneo_id=1, jugador1_id=1, jugador2_id=2, ganador_id=1,
        estado=estado, ronda=ronda, orden=orden, es_pase_libre=False,
        to_dict=lambda: {"id": 1},
    )


def torneo(modo):
    return SimpleNamespace(id=1, modo=modo)


def test_en_todos_contra_todos_siempre_se_puede_corregir():
    """Los partidos están definidos de antemano: cambiar quién ganó solo
    recalcula la tabla."""
    permitido, _ = partido_service.puede_corregirse(
        torneo("todos_contra_todos"), partido()
    )

    assert permitido


def test_en_eliminacion_no_se_puede_si_ya_se_genero_lo_que_sigue():
    """El ganador pasó a la ronda siguiente: cambiarlo dejaría partidos
    jugados por alguien que ya no ganó."""
    posteriores = [partido(orden=5)]

    with patch.object(partido_service.partido_repository, "obtener_por_torneo",
                      return_value=posteriores):
        permitido, motivo = partido_service.puede_corregirse(
            torneo("eliminacion"), partido(ronda=1, orden=1)
        )

    assert not permitido
    assert "inconsistente" in motivo


def test_en_eliminacion_se_puede_si_es_el_ultimo():
    """Nada depende todavía de ese resultado."""
    with patch.object(partido_service.partido_repository, "obtener_por_torneo",
                      return_value=[partido(orden=1)]):
        permitido, _ = partido_service.puede_corregirse(
            torneo("eliminacion"), partido(ronda=1, orden=1)
        )

    assert permitido


def test_un_partido_sin_jugar_siempre_se_puede_cargar():
    permitido, _ = partido_service.puede_corregirse(
        torneo("eliminacion"), partido(estado="pendiente")
    )

    assert permitido


def test_corregir_valida_que_el_ganador_haya_jugado():
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=partido()), \
         patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo("todos_contra_todos")):
        with pytest.raises(partido_service.ResultadoInvalidoError, match="ganador"):
            partido_service.corregir_resultado(1, ganador_id=99)


def test_corregir_rechaza_rondas_invalidas():
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=partido()), \
         patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo("todos_contra_todos")):
        with pytest.raises(partido_service.ResultadoInvalidoError, match="rondas"):
            partido_service.corregir_resultado(1, ganador_id=1, rondas_jugadas=7)


def test_corregir_guarda_el_resultado_nuevo():
    with patch.object(partido_service.partido_repository, "obtener_por_id",
                      return_value=partido()), \
         patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo("todos_contra_todos")), \
         patch.object(partido_service.partido_repository,
                      "registrar_resultado") as registrar:
        partido_service.corregir_resultado(1, ganador_id=2, rondas_jugadas=3)

    assert registrar.call_args[0][1] == 2


def test_los_pases_libres_no_son_corregibles():
    """No se jugaron: no hay resultado que corregir."""
    pase_libre = partido()
    pase_libre.es_pase_libre = True

    with patch.object(partido_service.torneo_repository, "obtener_por_id",
                      return_value=torneo("eliminacion")), \
         patch.object(partido_service.partido_repository, "obtener_por_torneo",
                      return_value=[pase_libre]):
        assert partido_service.listar_corregibles(1) == []
