"""
Reglas de negocio de partidos.

Dos responsabilidades: armar el fixture cuando arranca un torneo, y
registrar resultados a medida que se juegan.
"""
from repositories import partido_repository, torneo_repository
from services import bracket_service, fixture_service


class PartidoNoEncontradoError(Exception):
    pass


class ResultadoInvalidoError(Exception):
    pass


def generar_fixture(torneo_id, modo, jugadores_ids):
    """
    Arma los partidos iniciales del torneo y lo pasa a 'en curso'.

    Cuánto se puede generar de antemano depende del formato, y esa es la
    diferencia de fondo entre los dos:

    - En todos contra todos se sabe desde el arranque quién juega contra
      quién, así que se genera el fixture completo. Eso permite mostrar
      todo lo que falta y estimar cuánto queda.

    - En eliminación solo se puede armar la primera ronda: quién juega en
      la segunda depende de quién gane en la primera. El resto se va
      generando a medida que se cargan resultados.
    """
    if modo == "eliminacion":
        return _generar_eliminacion(torneo_id, jugadores_ids)
    return _generar_todos_contra_todos(torneo_id, jugadores_ids)


def _generar_todos_contra_todos(torneo_id, jugadores_ids):
    jornadas = fixture_service.fixture_round_robin(jugadores_ids)

    partidos = []
    orden = 1
    for numero_jornada, jornada in enumerate(jornadas, start=1):
        for jugador1, jugador2 in jornada:
            partidos.append({
                "torneo_id": torneo_id,
                "jugador1_id": jugador1,
                "jugador2_id": jugador2,
                "orden": orden,
                "jornada": numero_jornada,
            })
            orden += 1

    partido_repository.crear_muchos(partidos)
    torneo_repository.cambiar_estado(torneo_id, "en_curso")
    return len(partidos)


def listar_partidos(torneo_id):
    return [p.to_dict() for p in partido_repository.obtener_por_torneo(torneo_id)]


def obtener_partido_actual(torneo_id):
    """El próximo partido a jugar, o None si ya se jugaron todos."""
    partido = partido_repository.obtener_siguiente_pendiente(torneo_id)
    return partido.to_dict() if partido else None


def cargar_resultado(partido_id, ganador_id, peleador1_id=None,
                     peleador2_id=None, rondas_jugadas=None):
    """
    Registra quién ganó un partido.

    Los personajes y las rondas son opcionales: en un torneo en vivo se
    cargan si hay tiempo, y las estadísticas que dependen de ellos
    simplemente no aparecen cuando faltan. Obligarlos haría que cargar un
    resultado sea más lento que jugar el partido.
    """
    partido = partido_repository.obtener_por_id(partido_id)
    if partido is None:
        raise PartidoNoEncontradoError(f"No existe el partido {partido_id}")

    # El ganador tiene que ser uno de los dos que jugaron. Sin esta
    # validación, un id equivocado dejaría un partido con un ganador que
    # ni siquiera participó, y eso rompería las estadísticas en silencio.
    if ganador_id not in (partido.jugador1_id, partido.jugador2_id):
        raise ResultadoInvalidoError(
            "El ganador tiene que ser uno de los dos jugadores del partido"
        )

    if rondas_jugadas is not None and rondas_jugadas not in (2, 3):
        raise ResultadoInvalidoError(
            "Las rondas jugadas solo pueden ser 2 (barrida) o 3 (cerrado)"
        )

    partido_repository.registrar_resultado(
        partido_id, ganador_id, peleador1_id, peleador2_id, rondas_jugadas
    )

    # En eliminación, terminar una ronda genera la siguiente. Se hace acá
    # y no en un paso aparte para que el torneo avance solo a medida que
    # se cargan resultados, sin que nadie tenga que pedirlo.
    if partido.ronda is not None:
        _avanzar_bracket(partido.torneo_id, partido.ronda)

    # Cuando no queda ningún partido pendiente, el torneo terminó. Se
    # decide acá y no desde afuera para que nadie tenga que acordarse de
    # cerrar el torneo a mano.
    if not partido_repository.quedan_pendientes(partido.torneo_id):
        torneo_repository.cambiar_estado(partido.torneo_id, "finalizado")

    return partido_repository.obtener_por_id(partido_id).to_dict()


def _generar_eliminacion(torneo_id, jugadores_ids):
    """Crea solo la primera ronda del cuadro."""
    cruces = bracket_service.sembrar_primera_ronda(jugadores_ids)

    partidos = []
    orden = 1
    for jugador1, jugador2 in cruces:
        # Los pases libres se guardan como partido igual, marcados y ya
        # finalizados. Podrían no guardarse -- no se juegan -- pero
        # entonces habría que llevar en otro lado la lista de quiénes
        # pasaron, y el avance del cuadro tendría dos fuentes de verdad.
        # Así tiene una sola: los partidos de la ronda.
        es_pase_libre = jugador2 is None
        partidos.append({
            "torneo_id": torneo_id,
            "jugador1_id": jugador1,
            "jugador2_id": jugador2,
            "orden": orden,
            "jornada": None,
            "ronda": 1,
            "es_pase_libre": es_pase_libre,
            # El que pasa libre es su propio ganador: no hay nada que
            # cargar y la ronda no debería quedar esperándolo.
            "ganador_id": jugador1 if es_pase_libre else None,
            "estado": "finalizado" if es_pase_libre else "pendiente",
        })
        orden += 1

    partido_repository.crear_muchos(partidos, con_ronda=True)
    torneo_repository.cambiar_estado(torneo_id, "en_curso")
    return sum(1 for p in partidos if not p["es_pase_libre"])


def _avanzar_bracket(torneo_id, ronda):
    """Si la ronda terminó, genera la siguiente con los ganadores."""
    partidos_ronda = partido_repository.obtener_por_ronda(torneo_id, ronda)
    if any(p.estado != "finalizado" for p in partidos_ronda):
        return  # todavía falta jugar alguno

    # Los pases libres ya están entre estos partidos, con su ganador
    # cargado: no hay que buscarlos aparte. Y como vienen ordenados por
    # el orden del cuadro, los mejor sembrados quedan adelante y mantienen
    # la ventaja de su siembra.
    ganadores = [p.ganador_id for p in partidos_ronda]

    if len(ganadores) <= 1:
        return  # ya hay campeón, no hay ronda siguiente

    orden = partido_repository.obtener_max_orden(torneo_id)
    partidos = []
    for i in range(0, len(ganadores), 2):
        orden += 1
        partidos.append({
            "torneo_id": torneo_id,
            "jugador1_id": ganadores[i],
            "jugador2_id": ganadores[i + 1],
            "orden": orden,
            "jornada": None,
            "ronda": ronda + 1,
            "es_pase_libre": False,
            "ganador_id": None,
            "estado": "pendiente",
        })
    partido_repository.crear_muchos(partidos, con_ronda=True)
