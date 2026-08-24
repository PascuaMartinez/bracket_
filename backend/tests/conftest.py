"""
Configuración común de las pruebas.

El cache vive en memoria del proceso, y pytest corre todas las pruebas en
el mismo proceso: sin limpiarlo, una prueba recibiría el resultado que
guardó la anterior y el resultado dependería del orden en que se corran.
"""
import pytest

from services import cache


@pytest.fixture(autouse=True)
def cache_limpio():
    """autouse: se aplica a todas las pruebas sin que haya que pedirlo.

    Si dependiera de que cada prueba se acuerde de limpiarlo, alcanzaría
    con olvidarse en una para que aparezcan fallas intermitentes -- de las
    más difíciles de diagnosticar, porque cambian según el orden."""
    cache.invalidar_todo()
    yield
    cache.invalidar_todo()
