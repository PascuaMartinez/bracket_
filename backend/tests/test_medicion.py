"""
Pruebas de la instrumentación.

No prueban rendimiento -- eso depende de la máquina -- sino que el
contador funcione, que es lo que después permite medir de verdad.
"""
from database.medicion import contador, registrar


def test_cuenta_las_consultas():
    with contador() as c:
        registrar("SELECT * FROM jugador")
        registrar("SELECT * FROM torneo")

    assert c.total == 2


def test_agrupa_las_consultas_repetidas():
    """Una consulta que aparece muchas veces suele estar adentro de un
    bucle, que es justo lo que se quiere detectar."""
    with contador() as c:
        for _ in range(5):
            registrar("SELECT * FROM partido WHERE torneo_id = %s")

    consulta, veces = c.resumen()[0]
    assert veces == 5


def test_normaliza_los_espacios():
    """Las consultas escritas en varias líneas tienen que agruparse con
    las equivalentes, o cada una contaría por separado."""
    with contador() as c:
        registrar("SELECT *\n   FROM jugador")
        registrar("SELECT * FROM jugador")

    assert len(c.resumen()) == 1


def test_fuera_de_una_medicion_no_hace_nada():
    """La llamada queda puesta en la capa de datos siempre: tiene que ser
    inofensiva cuando nadie está midiendo."""
    registrar("SELECT 1")   # no debe fallar


def test_cada_medicion_arranca_de_cero():
    with contador() as primera:
        registrar("SELECT 1")

    with contador() as segunda:
        registrar("SELECT 2")

    assert primera.total == 1
    assert segunda.total == 1
