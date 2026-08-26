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


# --- Enfrentamiento directo ---

def partido_de_grupo(jugador1, jugador2, ganador):
    return SimpleNamespace(
        jugador1_id=jugador1, jugador2_id=jugador2, ganador_id=ganador,
        estado="finalizado", ronda=None, es_desempate=False,
    )


def test_dos_empatados_se_resuelven_por_lo_que_ya_jugaron():
    """Si ya se enfrentaron en el grupo, hacerlos jugar de nuevo sería
    ignorar ese resultado."""
    from services.grupos_service import resolver_por_enfrentamiento_directo

    bloques = resolver_por_enfrentamiento_directo(
        [1, 2], [partido_de_grupo(1, 2, ganador=1)]
    )

    assert bloques == [[1], [2]]


def test_el_triangular_perfecto_no_se_resuelve_asi():
    """Cada uno ganó uno y perdió uno: no hay nada en el grupo que los
    separe."""
    from services.grupos_service import resolver_por_enfrentamiento_directo

    bloques = resolver_por_enfrentamiento_directo(
        [1, 2, 3],
        [partido_de_grupo(1, 2, 1), partido_de_grupo(2, 3, 2), partido_de_grupo(3, 1, 3)],
    )

    assert bloques == [[1, 2, 3]]


def test_puede_resolver_parcialmente():
    """Uno queda definido y los otros siguen empatados: solo esos vuelven
    a jugar, porque el primero ya se ganó su lugar."""
    from services.grupos_service import resolver_por_enfrentamiento_directo

    bloques = resolver_por_enfrentamiento_directo(
        [1, 2, 3], [partido_de_grupo(1, 2, 1), partido_de_grupo(1, 3, 1)]
    )

    assert bloques == [[1], [2, 3]]


def test_los_partidos_contra_terceros_no_cuentan():
    """Lo que hicieron contra otros no dice nada sobre cómo se ordenan
    entre sí."""
    from services.grupos_service import resolver_por_enfrentamiento_directo

    bloques = resolver_por_enfrentamiento_directo(
        [1, 2],
        [partido_de_grupo(1, 9, ganador=1), partido_de_grupo(2, 9, ganador=9)],
    )

    # Ninguno le ganó al otro: siguen empatados pese a records distintos
    # contra el jugador 9.
    assert bloques == [[1, 2]]


# --- Repechaje ---

def test_los_cupos_sugeridos_dan_un_cuadro_limpio():
    """Una potencia de dos evita los pases libres, que le dan ventaja a
    algunos sin haberla ganado."""
    from services.grupos_service import cupos_sugeridos

    for cantidad in (10, 11, 12):
        assert cupos_sugeridos(cantidad, 2) == 4
    for cantidad in (13, 14, 15, 16):
        assert cupos_sugeridos(cantidad, 3) == 8


def test_los_cupos_sugeridos_dejan_gente_afuera():
    """Si clasifican casi todos, la fase de grupos no decide nada."""
    from services.grupos_service import cupos_sugeridos

    for cantidad in (10, 13, 20, 32):
        assert cupos_sugeridos(cantidad, 2) < cantidad


def test_no_sugiere_menos_de_dos():
    from services.grupos_service import cupos_sugeridos

    assert cupos_sugeridos(3, 1) >= 2


def test_detecta_cuando_sobran_lugares():
    """15 jugadores en 3 grupos con 8 cupos: pasan 2 por grupo y quedan 2
    en disputa."""
    from services.grupos_service import hay_repechaje

    por_grupo, sobrantes = hay_repechaje(8, [5, 5, 5])

    assert por_grupo == 2
    assert sobrantes == 2


def test_sin_sobrantes_no_hay_repechaje():
    from services.grupos_service import hay_repechaje

    por_grupo, sobrantes = hay_repechaje(8, [4, 4, 4, 4])

    assert por_grupo == 2
    assert sobrantes == 0
