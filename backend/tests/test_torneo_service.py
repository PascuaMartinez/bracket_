"""
Pruebas de las reglas de creación de un torneo.

Cada regla tiene su caso: son las que impiden que entre al sistema un
torneo que después no se puede jugar.
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import torneo_service


DATOS_BASE = {
    "nombre": "Copa",
    "modo": "todos_contra_todos",
    "fecha": date(2026, 5, 1),
    "jugadores_ids": [1, 2, 3],
}


def crear(**cambios):
    """Crea un torneo con los datos base, salvo lo que se pise. Los
    repositorios y la generación del fixture van sustituidos: acá lo que
    se prueba son las validaciones, no que se guarde."""
    datos = {**DATOS_BASE, **cambios}
    with patch.object(torneo_service.torneo_repository, "existe_sin_finalizar",
                      return_value=cambios.pop("_hay_torneo_abierto", False)), \
         patch.object(torneo_service.jugador_repository, "obtener_por_id",
                      side_effect=lambda jid: SimpleNamespace(id=jid)), \
         patch.object(torneo_service.torneo_repository, "crear", return_value=1), \
         patch.object(torneo_service.torneo_repository, "inscribir_jugadores"), \
         patch.object(torneo_service.torneo_repository, "obtener_por_id",
                      return_value=SimpleNamespace(to_dict=lambda: {"id": 1})), \
         patch("services.partido_service.generar_fixture"):
        return torneo_service.crear_torneo(**datos)


def test_crea_un_torneo_valido():
    assert crear() == {"id": 1}


def test_rechaza_nombre_vacio():
    with pytest.raises(torneo_service.TorneoInvalidoError, match="nombre"):
        crear(nombre="   ")


def test_rechaza_modo_desconocido():
    """Sin esta validación llegaría a la base un modo que ningún código
    sabe jugar, y el torneo quedaría inservible."""
    with pytest.raises(torneo_service.TorneoInvalidoError, match="Modo"):
        crear(modo="inventado")


def test_rechaza_jugadores_repetidos():
    """Un jugador anotado dos veces terminaría jugando contra sí mismo."""
    with pytest.raises(torneo_service.TorneoInvalidoError, match="repetidos"):
        crear(jugadores_ids=[1, 2, 2])


def test_rechaza_menos_del_minimo_de_jugadores():
    with pytest.raises(torneo_service.TorneoInvalidoError, match="al menos"):
        crear(jugadores_ids=[1, 2])


def test_rechaza_un_jugador_que_no_existe():
    with patch.object(torneo_service.torneo_repository, "existe_sin_finalizar",
                      return_value=False), \
         patch.object(torneo_service.jugador_repository, "obtener_por_id",
                      side_effect=lambda jid: None if jid == 99 else SimpleNamespace(id=jid)):
        with pytest.raises(torneo_service.TorneoInvalidoError, match="99"):
            torneo_service.crear_torneo(**{**DATOS_BASE, "jugadores_ids": [1, 2, 99]})


def test_rechaza_si_ya_hay_un_torneo_sin_finalizar():
    """La app acompaña un torneo mientras se juega: con dos abiertos sería
    ambiguo a cuál se le está cargando cada resultado."""
    with patch.object(torneo_service.torneo_repository, "existe_sin_finalizar",
                      return_value=True):
        with pytest.raises(torneo_service.TorneoInvalidoError, match="sin finalizar"):
            torneo_service.crear_torneo(**DATOS_BASE)
