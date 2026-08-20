"""
Pruebas de la puntuación de rey de la cancha.

Las pruebas están escritas contra las intenciones del formato, no contra
los números que da la fórmula: si mañana se ajustan los pesos, lo que
tiene que seguir siendo cierto es que las rachas pesen más que el aguante
y que el campeón vaya primero.
"""
import pytest

from services.rey_de_la_cancha_service import (
    calcular_puntos_racha, calcular_tabla, puntos_de_racha,
)


def jugador(nombre, puntos_racha, orden_eliminacion=None, eliminado=True):
    return {
        "jugador_id": abs(hash(nombre)) % 1000,
        "nombre": nombre,
        "puntos_racha": puntos_racha,
        "orden_eliminacion": orden_eliminacion,
        "eliminado": eliminado,
    }


@pytest.mark.parametrize("largo,puntos", [(0, 0), (1, 1), (2, 4), (3, 9), (4, 16)])
def test_una_racha_vale_su_largo_al_cuadrado(largo, puntos):
    assert puntos_de_racha(largo) == puntos


def test_las_victorias_seguidas_valen_mas_que_las_sueltas():
    """La razón de ser de la escala cuadrática: cada victoria seguida es
    más difícil que la anterior, porque el que está en cancha se desgasta
    y enfrenta rivales descansados."""
    sueltas = calcular_puntos_racha([True, False, True, False, True, False, True])
    seguidas = calcular_puntos_racha([True, True, True, True])

    assert seguidas > sueltas


def test_la_racha_abierta_al_final_tambien_cuenta():
    """El campeón nunca pierde: sin contar la racha que quedaba abierta,
    su mejor racha no sumaría nada."""
    assert calcular_puntos_racha([True, True, True]) == 9


def test_sin_partidos_no_suma():
    assert calcular_puntos_racha([]) == 0


def test_el_campeon_siempre_va_primero():
    """Ganó el torneo: una fórmula que lo pusiera segundo estaría midiendo
    mal, por más que los números den otra cosa."""
    tabla = calcular_tabla([
        jugador("Campeón", puntos_racha=1, eliminado=False),
        jugador("Otro", puntos_racha=25, orden_eliminacion=3),
    ])

    assert tabla[0]["nombre"] == "Campeón"
    assert tabla[0]["puesto"] == 1


def test_la_racha_pesa_mas_que_haber_aguantado():
    """Alguien puede sobrevivir mucho rato sin ganar nunca, solo porque la
    cola es larga y le tocan pocos turnos."""
    tabla = calcular_tabla([
        jugador("Rachero", puntos_racha=16, orden_eliminacion=1),
        jugador("Aguantó", puntos_racha=1, orden_eliminacion=5),
    ])

    assert tabla[0]["nombre"] == "Rachero"


def test_entre_rachas_parecidas_desempata_haber_llegado_mas_lejos():
    tabla = calcular_tabla([
        jugador("Temprano", puntos_racha=4, orden_eliminacion=1),
        jugador("Tarde", puntos_racha=4, orden_eliminacion=5),
    ])

    assert tabla[0]["nombre"] == "Tarde"


def test_los_que_empatan_comparten_puesto():
    tabla = calcular_tabla([
        jugador("Ana", puntos_racha=4, orden_eliminacion=2),
        jugador("Beto", puntos_racha=4, orden_eliminacion=2),
    ])

    assert tabla[0]["puesto"] == tabla[1]["puesto"]


def test_sin_jugadores_devuelve_vacio():
    assert calcular_tabla([]) == []


def test_un_solo_jugador_sin_eliminar_no_falla():
    """El caso que rompería al normalizar: no hay eliminados, así que los
    máximos son cero y habría una división por cero."""
    tabla = calcular_tabla([jugador("Único", puntos_racha=0, eliminado=False)])

    assert len(tabla) == 1
    assert tabla[0]["puesto"] == 1
