"""
Pruebas de los desempates en el corte de clasificación.

Un empate se resuelve donde corresponde -- jugando -- y no con un
criterio inventado. Lo que se protege acá es que esos partidos se generen
bien y que no ensucien las estadísticas.
"""
from types import SimpleNamespace
from unittest.mock import patch

from services import partido_service


def partido(jugador1, jugador2, ganador=None):
    return SimpleNamespace(
        jugador1_id=jugador1, jugador2_id=jugador2, ganador_id=ganador,
        es_desempate=True, estado="finalizado" if ganador else "pendiente",
    )


def generar(empatados):
    with patch.object(partido_service.partido_repository, "obtener_max_orden",
                      return_value=0), \
         patch.object(partido_service.partido_repository, "crear_muchos") as crear:
        partido_service._generar_desempate(1, empatados)
    return crear.call_args[0][0]


def test_dos_empatados_juegan_un_partido():
    partidos = generar([1, 2])

    assert len(partidos) == 1
    assert {partidos[0]["jugador1_id"], partidos[0]["jugador2_id"]} == {1, 2}


def test_tres_empatados_juegan_todos_contra_todos():
    """Es la única forma de ordenarlos sin que alguno tenga ventaja:
    hacer jugar a dos y que el tercero pase gratis lo premiaría por no
    jugar."""
    partidos = generar([1, 2, 3])

    assert len(partidos) == 3
    cruces = {frozenset([p["jugador1_id"], p["jugador2_id"]]) for p in partidos}
    assert cruces == {frozenset([1, 2]), frozenset([1, 3]), frozenset([2, 3])}


def test_los_partidos_quedan_marcados_como_desempate():
    """Es lo que después los excluye de las estadísticas."""
    partidos = generar([1, 2])

    assert all(p["es_desempate"] for p in partidos)


def test_el_desempate_ordena_por_lo_que_paso_en_el_desempate():
    desempates = [partido(1, 2, ganador=1), partido(1, 3, ganador=1),
                  partido(2, 3, ganador=2)]

    orden = partido_service._ordenar_por_desempate(desempates, {1, 2, 3})

    assert orden == [1, 2, 3]


def test_si_el_desempate_no_separa_devuelve_nada():
    """Con tres jugadores puede pasar que cada uno gane uno y pierda uno.
    Volver a jugar lo mismo no cambiaría nada, así que lo decide el
    organizador."""
    desempates = [partido(1, 2, ganador=1), partido(2, 3, ganador=2),
                  partido(3, 1, ganador=3)]

    assert partido_service._ordenar_por_desempate(desempates, {1, 2, 3}) is None


def test_dos_empatados_siempre_se_separan():
    """Con dos, alguno gana: no hay forma de que quede sin resolver."""
    orden = partido_service._ordenar_por_desempate(
        [partido(1, 2, ganador=2)], {1, 2}
    )

    assert orden == [2, 1]
