"""
Pruebas de la tabla de posiciones de un torneo.

Acá sí hace falta sustituir los repositorios, porque el cálculo lee
participantes y partidos. Que eso se pueda hacer con dos mocks -- en vez
de tener que levantar una base con datos -- es la ventaja concreta de
separar el acceso a datos en su propia capa.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services import tabla_service


def participante(jugador_id, nombre):
    return {"jugador_id": jugador_id, "nombre": nombre, "torneo_jugador_id": jugador_id}


def partido(jugador1, jugador2, ganador, estado="finalizado"):
    return SimpleNamespace(
        jugador1_id=jugador1, jugador2_id=jugador2,
        ganador_id=ganador, estado=estado,
    )


def calcular(participantes, partidos):
    with patch.object(tabla_service.torneo_repository, "obtener_participantes",
                      return_value=participantes), \
         patch.object(tabla_service.partido_repository, "obtener_por_torneo",
                      return_value=partidos):
        return tabla_service.calcular_tabla(torneo_id=1)


def test_ordena_por_puntos():
    participantes = [participante(1, "Ana"), participante(2, "Beto"), participante(3, "Caro")]
    partidos = [
        partido(1, 2, ganador=1),
        partido(1, 3, ganador=1),
        partido(2, 3, ganador=2),
    ]

    tabla = calcular(participantes, partidos)

    assert [f["nombre"] for f in tabla] == ["Ana", "Beto", "Caro"]
    assert [f["puntos"] for f in tabla] == [2, 1, 0]


def test_los_que_empatan_comparten_puesto_sin_saltear_numeros():
    """Puesto denso: 1, 1, 2 y no 1, 1, 3."""
    participantes = [participante(1, "Ana"), participante(2, "Beto"), participante(3, "Caro")]
    # Ana y Beto ganan uno cada uno; Caro pierde los dos.
    partidos = [partido(1, 3, ganador=1), partido(2, 3, ganador=2)]

    tabla = calcular(participantes, partidos)

    assert [f["puesto"] for f in tabla] == [1, 1, 2]


def test_el_win_rate_desempata_pero_no_ordena():
    """Alguien con menos puntos no puede pasar adelante por tener mejor
    proporción: en un torneo vale cuánto ganaste, no en qué proporción."""
    participantes = [participante(1, "Ana"), participante(2, "Beto"), participante(3, "Caro")]
    # Ana gana 2 de 2 (100%). Beto gana 1 de 1 (100%) pero jugó menos.
    partidos = [
        partido(1, 2, ganador=1),
        partido(1, 3, ganador=1),
        partido(2, 3, ganador=2),
    ]

    tabla = calcular(participantes, partidos)

    assert tabla[0]["nombre"] == "Ana"
    assert tabla[0]["puntos"] > tabla[1]["puntos"]


def test_los_partidos_sin_jugar_no_cuentan():
    participantes = [participante(1, "Ana"), participante(2, "Beto")]
    partidos = [
        partido(1, 2, ganador=1),
        partido(1, 2, ganador=None, estado="pendiente"),
    ]

    tabla = calcular(participantes, partidos)

    assert tabla[0]["pj"] == 1


def test_los_participantes_sin_partidos_aparecen_en_cero():
    """Alguien anotado que todavía no jugó tiene que estar en la tabla,
    no ausente hasta que gane algo."""
    participantes = [participante(1, "Ana"), participante(2, "Beto"), participante(3, "Caro")]

    tabla = calcular(participantes, partidos=[])

    assert len(tabla) == 3
    assert all(f["pj"] == 0 and f["puntos"] == 0 for f in tabla)
    # Todos empatados en cero comparten el primer puesto.
    assert all(f["puesto"] == 1 for f in tabla)


def test_win_rate_sin_partidos_jugados_es_cero_y_no_falla():
    """El caso que rompería con una división por cero."""
    tabla = calcular([participante(1, "Ana")], partidos=[])

    assert tabla[0]["win_rate"] == 0


@pytest.mark.parametrize("ganador,esperado_ana,esperado_beto", [
    (1, (1, 0), (0, 1)),
    (2, (0, 1), (1, 0)),
])
def test_cuenta_ganados_y_perdidos_de_los_dos_lados(ganador, esperado_ana, esperado_beto):
    """El ganador se guarda como referencia y no como 'ganó el jugador 1',
    así que contar bien no debe depender de qué lado le tocó a cada uno."""
    participantes = [participante(1, "Ana"), participante(2, "Beto")]

    tabla = calcular(participantes, [partido(1, 2, ganador=ganador)])

    por_nombre = {f["nombre"]: f for f in tabla}
    assert (por_nombre["Ana"]["pg"], por_nombre["Ana"]["pp"]) == esperado_ana
    assert (por_nombre["Beto"]["pg"], por_nombre["Beto"]["pp"]) == esperado_beto
