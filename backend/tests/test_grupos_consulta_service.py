"""
Pruebas de qué se ofrece en cada momento de un empate en grupos.

Hay tres estados posibles y cada uno habilita algo distinto:
- la fase de grupos sigue en curso: nadie está "en disputa" todavía
- terminó con empate y el desempate está pendiente: hay que ir a jugarlo
- el desempate se jugó y no separó: recién ahí se puede forzar a mano
"""
from types import SimpleNamespace
from unittest.mock import patch

from services import grupos_consulta_service as gcs


def partido(j1, j2, ronda=None, es_desempate=False, estado="pendiente"):
    return SimpleNamespace(jugador1_id=j1, jugador2_id=j2, ronda=ronda,
                           es_desempate=es_desempate, estado=estado)


def calcular(partidos, jugadores, tabla):
    with patch.object(gcs.grupo_repository, "obtener_por_torneo",
                      return_value=[{"id": 1, "nombre": "Grupo A"}]), \
         patch.object(gcs.grupo_repository, "obtener_jugadores", return_value=jugadores), \
         patch.object(gcs.tabla_service, "calcular_tabla_de_grupo", return_value=tabla), \
         patch.object(gcs.partido_repository, "obtener_por_torneo", return_value=partidos):
        return gcs.obtener_grupos(1)[0]["tabla"]


def test_un_torneo_recien_creado_no_muestra_a_nadie_en_disputa():
    """Con la fase de grupos sin jugar todavía, todos tienen 'clasificado'
    en None -- pero eso no es un empate, es que no se sabe nada aún."""
    jugadores = [{"jugador_id": i, "nombre": n, "clasificado": None}
                 for i, n in [(1, "Ana"), (2, "Beto")]]
    tabla = [{"jugador_id": i, "nombre": n, "puesto": 1, "pj": 0, "pg": 0, "pp": 0,
             "puntos": 0} for i, n in [(1, "Ana"), (2, "Beto")]]
    partidos = [partido(1, 2, estado="pendiente")]

    filas = calcular(partidos, jugadores, tabla)

    assert all(not f["sin_resolver"] for f in filas)
    assert all(not f["puede_forzarse"] for f in filas)


def test_fase_terminada_con_desempate_pendiente_no_permite_forzar():
    """El desempate está generado pero no se jugó: hay que ir a jugarlo,
    no saltearlo desde el listado."""
    jugadores = [{"jugador_id": i, "nombre": n, "clasificado": None}
                 for i, n in [(2, "Beto"), (3, "Caro")]]
    tabla = [{"jugador_id": i, "nombre": n, "puesto": 2, "pj": 2, "pg": 1, "pp": 1,
             "puntos": 1} for i, n in [(2, "Beto"), (3, "Caro")]]
    partidos = [
        partido(2, 3, estado="finalizado"),
        partido(2, 3, es_desempate=True, estado="pendiente"),
    ]

    filas = calcular(partidos, jugadores, tabla)

    assert all(f["sin_resolver"] and not f["puede_forzarse"] for f in filas)


def test_desempate_jugado_sin_separar_si_permite_forzar():
    jugadores = [{"jugador_id": i, "nombre": n, "clasificado": None}
                 for i, n in [(2, "Beto"), (3, "Caro")]]
    tabla = [{"jugador_id": i, "nombre": n, "puesto": 2, "pj": 2, "pg": 1, "pp": 1,
             "puntos": 1} for i, n in [(2, "Beto"), (3, "Caro")]]
    partidos = [
        partido(2, 3, estado="finalizado"),
        partido(2, 3, es_desempate=True, estado="finalizado"),
    ]

    filas = calcular(partidos, jugadores, tabla)

    assert all(f["puede_forzarse"] for f in filas)
