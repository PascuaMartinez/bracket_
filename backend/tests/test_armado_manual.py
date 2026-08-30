"""
Pruebas del armado manual de torneos.

El reparto automático equilibra por nivel, que es lo correcto en general.
Pero quien organiza a veces sabe cosas que el sistema no, y lo que se
protege acá es que ese armado a mano no deje un torneo injugable.
"""
import pytest

from services.torneo_service import TorneoInvalidoError, _validar_grupos_manuales


def test_acepta_grupos_parejos():
    _validar_grupos_manuales([[1, 2], [3, 4]], [1, 2, 3, 4], cantidad_grupos=2)


def test_acepta_uno_de_diferencia():
    """Con cinco jugadores en dos grupos, alguno tiene que tener tres."""
    _validar_grupos_manuales([[1, 2, 3], [4, 5]], [1, 2, 3, 4, 5], cantidad_grupos=2)


def test_rechaza_grupos_desparejos():
    """El reparto de cupos y el repechaje asumen paridad: con seis en uno
    y dos en otro, clasificar sería mucho más difícil en uno que en otro
    y el sistema los trataría como equivalentes."""
    with pytest.raises(TorneoInvalidoError, match="parejos"):
        _validar_grupos_manuales(
            [[1, 2, 3, 4, 5, 6], [7, 8]], list(range(1, 9)), cantidad_grupos=2
        )


def test_rechaza_un_grupo_vacio():
    with pytest.raises(TorneoInvalidoError, match="vacío"):
        _validar_grupos_manuales([[1, 2, 3, 4], []], [1, 2, 3, 4], cantidad_grupos=2)


def test_rechaza_si_falta_alguien():
    """Quedaría fuera del torneo sin que nadie lo haya decidido."""
    with pytest.raises(TorneoInvalidoError, match="exactamente un grupo"):
        _validar_grupos_manuales([[1, 2], [3]], [1, 2, 3, 4], cantidad_grupos=2)


def test_rechaza_si_alguien_esta_repetido():
    """Jugaría dos veces contra rivales distintos en el mismo torneo."""
    with pytest.raises(TorneoInvalidoError, match="exactamente un grupo"):
        _validar_grupos_manuales([[1, 2], [2, 3]], [1, 2, 3], cantidad_grupos=2)


def test_rechaza_una_cantidad_de_grupos_distinta():
    with pytest.raises(TorneoInvalidoError, match="grupos"):
        _validar_grupos_manuales([[1, 2, 3, 4]], [1, 2, 3, 4], cantidad_grupos=2)
