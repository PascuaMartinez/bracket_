"""
Pruebas del motor de la cola.

Se prueba la función que decide quién entra a la cancha, que es la única
parte del motor que es lógica pura.
"""
from services.partido_service import _proximo_en_la_cola


def jugador(jugador_id, posicion, eliminado=False):
    return {"jugador_id": jugador_id, "posicion_cola": posicion, "eliminado": eliminado}


def test_entra_el_primero_de_la_fila():
    estado = [jugador(1, 0), jugador(2, 1), jugador(3, 2)]

    assert _proximo_en_la_cola(estado, en_cancha_id=1)["jugador_id"] == 2


def test_no_entra_el_que_ya_esta_en_cancha():
    """El que ganó se queda: no puede ser también su propio desafiante."""
    estado = [jugador(1, 0), jugador(2, 1)]

    assert _proximo_en_la_cola(estado, en_cancha_id=1)["jugador_id"] == 2


def test_los_eliminados_no_entran():
    estado = [jugador(1, 0), jugador(2, 1, eliminado=True), jugador(3, 2)]

    assert _proximo_en_la_cola(estado, en_cancha_id=1)["jugador_id"] == 3


def test_respeta_el_orden_de_la_cola_y_no_el_de_la_lista():
    """El que perdió vuelve al final: su posición cambia, y el orden en
    que vengan de la base no debería importar."""
    estado = [jugador(3, 5), jugador(2, 1), jugador(1, 0)]

    assert _proximo_en_la_cola(estado, en_cancha_id=1)["jugador_id"] == 2


def test_sin_nadie_esperando_devuelve_nada():
    """Cuando queda uno solo en pie no hay próximo partido."""
    estado = [jugador(1, 0), jugador(2, 1, eliminado=True)]

    assert _proximo_en_la_cola(estado, en_cancha_id=1) is None
