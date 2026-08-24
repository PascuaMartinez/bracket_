"""
Pruebas del cache.

Lo que más importa verificar no es que guarde -- eso es lo fácil -- sino
que se invalide cuando corresponde. Un cache que devuelve datos viejos es
peor que no tener cache: la aplicación miente sin ninguna señal de que
algo anda mal.
"""
from unittest.mock import patch

from services import cache


def setup_function():
    """Cada prueba arranca con el cache vacío: si no, el resultado
    dependería del orden en que se corran."""
    cache.invalidar_todo()


def test_calcula_la_primera_vez():
    llamadas = []

    resultado = cache.obtener("clave", lambda: llamadas.append(1) or "valor")

    assert resultado == "valor"
    assert len(llamadas) == 1


def test_no_recalcula_la_segunda_vez():
    llamadas = []

    def calcular():
        llamadas.append(1)
        return "valor"

    cache.obtener("clave", calcular)
    cache.obtener("clave", calcular)

    assert len(llamadas) == 1


def test_claves_distintas_no_se_pisan():
    cache.obtener("a", lambda: "valor de a")
    cache.obtener("b", lambda: "valor de b")

    assert cache.obtener("a", lambda: "no debería calcularse") == "valor de a"


def test_invalidar_obliga_a_recalcular():
    llamadas = []

    def calcular():
        llamadas.append(1)
        return len(llamadas)

    cache.obtener("clave", calcular)
    cache.invalidar_todo()
    cache.obtener("clave", calcular)

    assert len(llamadas) == 2


def test_invalidar_vacia_todas_las_claves():
    """Los resultados están encadenados: cargar un partido cambia la tabla
    del torneo, que cambia el histórico, que cambia las estadísticas.
    Vaciar solo una parte dejaría el resto inconsistente."""
    cache.obtener("a", lambda: "vieja")
    cache.obtener("b", lambda: "vieja")

    cache.invalidar_todo()

    assert cache.obtener("a", lambda: "nueva") == "nueva"
    assert cache.obtener("b", lambda: "nueva") == "nueva"


def test_lo_guardado_vence():
    """Red de seguridad: si alguna escritura no invalidara por un error,
    el cache se vacía solo en vez de mentir para siempre."""
    cache.obtener("clave", lambda: "vieja")

    # Se simula que pasó más tiempo del permitido.
    with patch.object(cache, "SEGUNDOS_DE_VIDA", -1):
        assert cache.obtener("clave", lambda: "nueva") == "nueva"
