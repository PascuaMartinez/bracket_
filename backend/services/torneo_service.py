"""
Reglas de negocio de torneos.

Crear un torneo no es solo insertar una fila: hay que validar el modo,
que los jugadores existan y que sean suficientes, y dejar inscripta la
participación de cada uno. Todo eso es una sola operación desde afuera.
"""
from repositories import (
    jugador_repository, partido_repository, torneo_repository,
)

# Por ahora solo el primer formato. La lista crece cuando se implementen
# los demás, y validar contra ella evita que llegue a la base un modo
# que ningún código sabe manejar.
MODOS_VALIDOS = ("todos_contra_todos", "eliminacion", "rey_de_la_cancha",
                 "grupos_eliminacion")

# Con menos de tres no hay torneo: dos jugadores es una serie de partidos
# entre ellos, y no hay tabla de posiciones que valga la pena.
MINIMO_JUGADORES = 3


class TorneoNoEncontradoError(Exception):
    pass


class TorneoInvalidoError(Exception):
    pass


def listar_torneos():
    return [t.to_dict() for t in torneo_repository.obtener_todos()]


def obtener_torneo(torneo_id):
    torneo = torneo_repository.obtener_por_id(torneo_id)
    if torneo is None:
        raise TorneoNoEncontradoError(f"No existe el torneo {torneo_id}")
    return torneo.to_dict()


def obtener_participantes(torneo_id):
    obtener_torneo(torneo_id)  # valida que exista
    return torneo_repository.obtener_participantes(torneo_id)


def crear_torneo(nombre, modo, fecha, jugadores_ids, descripcion=None, lugar=None,
                 vidas_iniciales=None, cantidad_grupos=None,
                 cupos_eliminacion=None):
    if not nombre or not nombre.strip():
        raise TorneoInvalidoError("El nombre del torneo es obligatorio")

    if modo not in MODOS_VALIDOS:
        raise TorneoInvalidoError(f"Modo desconocido: {modo}")

    if not fecha:
        raise TorneoInvalidoError("La fecha del torneo es obligatoria")

    # Se corta acá y no al terminar el torneo anterior: la app acompaña un
    # torneo mientras se juega, y con dos abiertos sería ambiguo a cuál se
    # le está cargando cada resultado.
    if torneo_repository.existe_sin_finalizar():
        raise TorneoInvalidoError(
            "Ya hay un torneo sin finalizar. Terminá ese antes de crear otro."
        )

    jugadores_ids = _validar_jugadores(jugadores_ids)

    # Sin vidas no hay forma de saber cuándo termina un torneo de rey de
    # la cancha: la cola giraría para siempre.
    if modo == "rey_de_la_cancha":
        if not vidas_iniciales or vidas_iniciales < 1:
            raise TorneoInvalidoError(
                "Rey de la cancha necesita una cantidad de vidas válida"
            )

    if modo == "grupos_eliminacion":
        if not cantidad_grupos or cantidad_grupos < 2:
            raise TorneoInvalidoError("Hacen falta al menos 2 grupos")
        if not cupos_eliminacion or cupos_eliminacion < 2:
            raise TorneoInvalidoError("Tienen que clasificar al menos 2 jugadores")
        if cupos_eliminacion > len(jugadores_ids):
            raise TorneoInvalidoError(
                "No pueden clasificar más jugadores de los que participan"
            )
        # Con más grupos que jugadores habría grupos vacíos.
        if cantidad_grupos > len(jugadores_ids):
            raise TorneoInvalidoError("Hay más grupos que jugadores")

    torneo_id = torneo_repository.crear(
        nombre.strip(), modo, fecha,
        (descripcion or "").strip() or None,
        (lugar or "").strip() or None,
        vidas_iniciales if modo == "rey_de_la_cancha" else None,
        cupos_eliminacion if modo == "grupos_eliminacion" else None,
    )
    torneo_repository.inscribir_jugadores(torneo_id, jugadores_ids)

    # El fixture se arma acá y no en un paso aparte: un torneo sin
    # partidos no sirve para nada, así que crearlo y generarlo son una
    # sola operación desde afuera. El import va adentro de la función
    # porque partido_service también necesita torneo_service, y a nivel
    # de módulo se trabarían entre sí.
    from services import partido_service
    partido_service.generar_fixture(
        torneo_id, modo, jugadores_ids, vidas_iniciales, cantidad_grupos
    )

    return obtener_torneo(torneo_id)


def actualizar_torneo(torneo_id, nombre, fecha, descripcion=None, lugar=None):
    if not nombre or not nombre.strip():
        raise TorneoInvalidoError("El nombre del torneo es obligatorio")
    actualizado = torneo_repository.actualizar(
        torneo_id, nombre.strip(), fecha,
        (descripcion or "").strip() or None,
        (lugar or "").strip() or None,
    )
    if not actualizado:
        raise TorneoNoEncontradoError(f"No existe el torneo {torneo_id}")
    return obtener_torneo(torneo_id)


def eliminar_torneo(torneo_id):
    if not torneo_repository.eliminar(torneo_id):
        raise TorneoNoEncontradoError(f"No existe el torneo {torneo_id}")


def _validar_jugadores(jugadores_ids):
    """Sin duplicados, que existan, y que alcancen para armar un torneo."""
    if not jugadores_ids:
        raise TorneoInvalidoError("Hay que anotar jugadores al torneo")

    # Un mismo jugador anotado dos veces jugaría contra sí mismo.
    unicos = list(dict.fromkeys(jugadores_ids))
    if len(unicos) != len(jugadores_ids):
        raise TorneoInvalidoError("Hay jugadores repetidos en la lista")

    if len(unicos) < MINIMO_JUGADORES:
        raise TorneoInvalidoError(
            f"Se necesitan al menos {MINIMO_JUGADORES} jugadores"
        )

    for jugador_id in unicos:
        if jugador_repository.obtener_por_id(jugador_id) is None:
            raise TorneoInvalidoError(f"No existe el jugador {jugador_id}")

    return unicos


def torneo_en_curso():
    """
    El torneo abierto con cuánto lleva jugado, o None.

    Sirve para avisar ANTES de que alguien llene el formulario de un
    torneo nuevo. Rechazarlo al final, después de elegir jugadores y
    formato, es hacerle perder el trabajo por una regla que se podía
    decir al principio.

    Se informa cuántos partidos van de cuántos porque es lo que permite
    decidir: "12 de 28" pesa distinto que "1 de 28".
    """
    torneo = torneo_repository.obtener_sin_finalizar()
    if torneo is None:
        return None

    partidos = partido_repository.obtener_por_torneo(torneo.id)
    jugados = [p for p in partidos if p.estado == "finalizado"]

    return {
        **torneo.to_dict(),
        "partidos_totales": len(partidos),
        "partidos_jugados": len(jugados),
    }
