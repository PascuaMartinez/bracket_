"""Pruebas de la configuración."""
from unittest.mock import patch

import pytest

from services import configuracion_service as config


def test_rechaza_un_nombre_de_club_vacio():
    with pytest.raises(config.ConfiguracionInvalidaError):
        config.actualizar("   ")


def test_rechaza_estadisticas_que_no_existen():
    """Una clave mal escrita quedaría guardada para siempre sin efecto, y
    nadie se enteraría de que está mal."""
    with pytest.raises(config.ConfiguracionInvalidaError, match="desconocidas"):
        config.guardar_estadisticas_ocultas(["jugador.inventada"])


def test_acepta_las_del_catalogo():
    with patch.object(config.configuracion_repository, "guardar_ocultas") as guardar:
        resultado = config.guardar_estadisticas_ocultas(["jugador.mejor_racha"])

    assert resultado == ["jugador.mejor_racha"]
    guardar.assert_called_once()


def test_el_filtro_saca_las_ocultas():
    datos = {"mejor_racha": 5, "win_rate": 0.6}

    with patch.object(config.configuracion_repository, "obtener_ocultas",
                      return_value={"jugador.mejor_racha"}):
        filtrado = config.filtrar_ocultas(datos, "jugador")

    assert "mejor_racha" not in filtrado
    assert filtrado["win_rate"] == 0.6


def test_el_filtro_distingue_por_prefijo():
    """'espejos' existe en personajes; ocultarla ahí no debería afectar a
    una estadística de jugador con el mismo nombre."""
    with patch.object(config.configuracion_repository, "obtener_ocultas",
                      return_value={"peleador.espejos"}):
        filtrado = config.filtrar_ocultas({"espejos": 3}, "jugador")

    assert filtrado["espejos"] == 3


def test_una_estadistica_nueva_aparece_visible():
    """Solo se guardan las ocultas: agregar una al catálogo no requiere
    tocar la base para que se vea."""
    with patch.object(config.configuracion_repository, "obtener_ocultas",
                      return_value=set()):
        estadisticas = config.listar_estadisticas()

    assert all(e["visible"] for e in estadisticas)
