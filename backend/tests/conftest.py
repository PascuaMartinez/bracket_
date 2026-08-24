"""
Configuración común de las pruebas.

El cache vive en memoria del proceso, y pytest corre todas las pruebas en
el mismo proceso: sin limpiarlo, una prueba recibiría el resultado que
guardó la anterior y el resultado dependería del orden en que se corran.
"""
import pytest

from unittest.mock import patch

from services import cache, configuracion_service


@pytest.fixture(autouse=True)
def cache_limpio():
    """autouse: se aplica a todas las pruebas sin que haya que pedirlo.

    Si dependiera de que cada prueba se acuerde de limpiarlo, alcanzaría
    con olvidarse en una para que aparezcan fallas intermitentes -- de las
    más difíciles de diagnosticar, porque cambian según el orden."""
    cache.invalidar_todo()
    yield
    cache.invalidar_todo()


@pytest.fixture(autouse=True)
def sin_estadisticas_ocultas():
    """Por defecto no hay ninguna oculta.

    El filtro de estadísticas consulta la base, y las pruebas del cálculo
    no deberían necesitar una base corriendo solo para averiguar que no
    hay nada escondido. Las pruebas que sí quieran probar el filtro pueden
    sustituirlo por su cuenta."""
    with patch.object(configuracion_service.configuracion_repository,
                      "obtener_ocultas", return_value=set()):
        yield
