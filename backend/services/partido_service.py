"""
Reglas de negocio de partidos.

Dos responsabilidades: armar el fixture cuando arranca un torneo, y
registrar resultados a medida que se juegan.
"""
from repositories import partido_repository, torneo_repository
from services import fixture_service


class PartidoNoEncontradoError(Exception):
    pass


class ResultadoInvalidoError(Exception):
    pass


def generar_fixture(torneo_id, jugadores_ids):
    """
    Arma todos los partidos del torneo y lo pasa a 'en curso'.

    El fixture se genera entero de una vez y no partido a partido: en
    todos contra todos se sabe desde el arranque quién juega contra quién,
    así que tenerlo completo permite mostrar lo que falta y estimar cuánto
    queda. (Formatos donde el próximo cruce depende del resultado anterior
    van a necesitar otra estrategia.)
    """
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

    # Cuando no queda ningún partido pendiente, el torneo terminó. Se
    # decide acá y no desde afuera para que nadie tenga que acordarse de
    # cerrar el torneo a mano.
    if not partido_repository.quedan_pendientes(partido.torneo_id):
        torneo_repository.cambiar_estado(partido.torneo_id, "finalizado")

    return partido_repository.obtener_por_id(partido_id).to_dict()
