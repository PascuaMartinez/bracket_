"""Pruebas de las estadísticas de personajes y del matchup parejo."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from services import estadisticas_peleador_service as eps
from services.estadisticas_service import _matchup_mas_parejo


def rival(nombre, ganados, perdidos):
    jugados = ganados + perdidos
    return {
        "nombre": nombre, "jugados": jugados, "ganados": ganados,
        "perdidos": perdidos,
        "win_rate": round(ganados / jugados, 3) if jugados else 0,
    }


def test_el_matchup_parejo_no_confunde_una_paliza_con_una_rivalidad():
    """Midiendo la diferencia bruta, un 0-3 (diferencia 3) le ganaría a un
    4-6 (diferencia 2), cuando el 0-3 es exactamente lo contrario de
    parejo."""
    rivales = [rival("Paliza", 0, 3), rival("Parejo", 4, 6)]

    resultado = _matchup_mas_parejo(rivales)

    assert [r["nombre"] for r in resultado] == ["Parejo"]


def test_el_matchup_parejo_prefiere_el_que_esta_mas_cerca_del_50():
    rivales = [rival("Cerca", 5, 5), rival("Lejos", 8, 2)]

    assert _matchup_mas_parejo(rivales)[0]["nombre"] == "Cerca"


def test_entre_dos_igual_de_parejos_gana_el_que_jugo_mas():
    """Un 5-5 dice más de una rivalidad pareja que un 2-2."""
    rivales = [rival("Pocos", 2, 2), rival("Muchos", 5, 5)]

    assert _matchup_mas_parejo(rivales)[0]["nombre"] == "Muchos"


def test_el_matchup_parejo_pide_un_minimo_de_partidos():
    """Con uno o dos partidos el resultado es azar, no una tendencia."""
    rivales = [rival("Uno", 1, 1)]

    assert _matchup_mas_parejo(rivales) == []


def test_sin_rivales_no_falla():
    assert _matchup_mas_parejo([]) == []


# --- Estadísticas de personaje ---

def partido(jugador1, jugador2, peleador1, peleador2, ganador,
            rondas=None, orden=1, es_pase_libre=False, es_desempate=False):
    return SimpleNamespace(
        jugador1_id=jugador1, jugador2_id=jugador2,
        jugador1_peleador_id=peleador1, jugador2_peleador_id=peleador2,
        ganador_id=ganador, rondas_jugadas=rondas, orden=orden,
        estado="finalizado", es_pase_libre=es_pase_libre, es_desempate=es_desempate,
    )


def calcular(partidos, peleador_id=1):
    peleadores = [SimpleNamespace(id=1, nombre="Sol"), SimpleNamespace(id=2, nombre="Ky")]
    jugadores = [SimpleNamespace(id=1, nombre="Ana"), SimpleNamespace(id=2, nombre="Beto")]

    with patch.object(eps.peleador_repository, "obtener_por_id",
                      return_value=peleadores[0]), \
         patch.object(eps.peleador_repository, "obtener_todos", return_value=peleadores), \
         patch.object(eps.jugador_repository, "obtener_todos", return_value=jugadores), \
         patch.object(eps.torneo_repository, "obtener_todos",
                      return_value=[SimpleNamespace(id=1, estado="finalizado",
                                                    nombre="Enero",
                                                    fecha=date(2026, 1, 1))]), \
         patch.object(eps.partido_repository, "obtener_por_torneo", return_value=partidos), \
         patch("services.tabla_service.calcular_tabla",
               return_value=[{"jugador_id": 1, "nombre": "Ana", "puesto": 1}]):
        return eps.obtener_estadisticas(peleador_id)


def test_cuenta_los_usos_de_los_dos_lados():
    """El personaje puede estar de cualquier lado del partido."""
    stats = calcular([
        partido(1, 2, peleador1=1, peleador2=2, ganador=1),
        partido(1, 2, peleador1=2, peleador2=1, ganador=2),
    ])

    assert stats["veces_usado"] == 2


def test_los_espejos_cuentan_partidos_y_no_apariciones():
    """Un partido donde los dos eligieron el mismo personaje genera dos
    apariciones, pero es un solo espejo."""
    stats = calcular([partido(1, 2, peleador1=1, peleador2=1, ganador=1)])

    assert stats["espejos"] == 1


def test_las_barridas_solo_cuentan_donde_se_registro_el_dato():
    """Las rondas son opcionales al cargar el resultado."""
    stats = calcular([
        partido(1, 2, peleador1=1, peleador2=2, ganador=1, rondas=2),
        partido(1, 2, peleador1=1, peleador2=2, ganador=1),   # sin registrar
    ])

    assert stats["barridas_a_favor"] == 1
    assert stats["veces_usado"] == 2


def test_los_pases_libres_no_cuentan():
    stats = calcular([
        partido(1, 2, peleador1=1, peleador2=2, ganador=1),
        partido(1, None, peleador1=1, peleador2=None, ganador=1, es_pase_libre=True),
    ])

    assert stats["veces_usado"] == 1


def test_sin_usos_no_falla():
    """El caso que rompería con una división por cero."""
    stats = calcular([])

    assert stats["veces_usado"] == 0
    assert stats["win_rate"] == 0
    assert stats["mas_usado_por"] == []


def test_registra_la_primera_y_la_ultima_vez_que_se_uso():
    """Un personaje con 30 usos pero ninguno reciente cuenta una historia
    distinta de uno con 30 repartidos hasta la semana pasada."""
    stats = calcular([partido(1, 2, peleador1=1, peleador2=2, ganador=1)])

    assert stats["primera_vez"]["torneo"] == "Enero"
    assert stats["ultima_vez"]["torneo"] == "Enero"


def test_el_mejor_resultado_mira_cada_jugador_y_torneo_una_sola_vez():
    """Alguien puede usar el mismo personaje en varios partidos del mismo
    torneo: su puesto es uno solo."""
    stats = calcular([
        partido(1, 2, peleador1=1, peleador2=2, ganador=1, orden=1),
        partido(1, 2, peleador1=1, peleador2=2, ganador=1, orden=2),
    ])

    assert stats["mejor_resultado"]["puesto"] == 1
    assert stats["mejor_resultado"]["jugador"] == "Ana"


def test_sin_usos_la_trayectoria_viene_vacia():
    stats = calcular([])

    assert stats["primera_vez"] is None
    assert stats["mejor_resultado"] is None
