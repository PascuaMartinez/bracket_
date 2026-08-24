"""Pruebas del historial de partidos."""
from datetime import date
from unittest.mock import patch

from services import historial_service


def fila(id=1, ganador_id=1):
    return {
        "id": id, "torneo_id": 1, "torneo_nombre": "Copa",
        "torneo_fecha": date(2026, 5, 1),
        "jugador1_id": 1, "jugador1_nombre": "Ana",
        "jugador2_id": 2, "jugador2_nombre": "Beto",
        "peleador1_nombre": "Sol", "peleador2_nombre": None,
        "ganador_id": ganador_id, "rondas_jugadas": 2,
    }


def buscar(filas, total, **kwargs):
    with patch.object(historial_service.partido_repository, "buscar",
                      return_value=(filas, total)) as mock:
        resultado = historial_service.buscar(**kwargs)
    return resultado, mock


def test_identifica_al_ganador_de_cada_lado():
    """Quien muestre la lista no debería tener que comparar ids."""
    resultado, _ = buscar([fila(ganador_id=1)], total=1)

    partido = resultado["partidos"][0]
    assert partido["jugador1"]["gano"] is True
    assert partido["jugador2"]["gano"] is False


def test_funciona_si_gano_el_segundo():
    resultado, _ = buscar([fila(ganador_id=2)], total=1)

    partido = resultado["partidos"][0]
    assert partido["jugador2"]["gano"] is True


def test_calcula_la_cantidad_de_paginas():
    resultado, _ = buscar([], total=120)

    # 120 partidos de a 50 son tres páginas: la última con 20.
    assert resultado["paginas"] == 3


def test_con_pocos_partidos_hay_una_sola_pagina():
    resultado, _ = buscar([], total=10)

    assert resultado["paginas"] == 1


def test_sin_partidos_igual_hay_una_pagina():
    """Cero páginas dejaría la pantalla en un estado sin sentido."""
    resultado, _ = buscar([], total=0)

    assert resultado["paginas"] == 1


def test_la_pagina_se_traduce_a_desplazamiento():
    _, mock = buscar([], total=0, pagina=3)

    assert mock.call_args.kwargs["desplazamiento"] == 100


def test_una_pagina_invalida_cae_en_la_primera():
    """Un número negativo en la dirección no debería romper la consulta."""
    resultado, mock = buscar([], total=0, pagina=-5)

    assert resultado["pagina"] == 1
    assert mock.call_args.kwargs["desplazamiento"] == 0
