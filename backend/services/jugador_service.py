"""
Reglas de negocio de jugadores.

La capa del medio: valida, decide y coordina. El controlador de arriba se
ocupa de HTTP y el repositorio de abajo de SQL; acá está lo que sigue
siendo verdad sin importar si esto se consume por web, por consola o por
otro programa.

Los errores se expresan como excepciones propias del dominio y no como
códigos HTTP: un servicio no tiene por qué saber que 404 existe. El
controlador traduce.
"""
from repositories import jugador_repository


class JugadorNoEncontradoError(Exception):
    pass


class JugadorInvalidoError(Exception):
    pass


def listar_jugadores(incluir_ocultos=False):
    return [j.to_dict() for j in jugador_repository.obtener_todos(incluir_ocultos)]


def obtener_jugador(jugador_id):
    jugador = jugador_repository.obtener_por_id(jugador_id)
    if jugador is None:
        raise JugadorNoEncontradoError(f"No existe el jugador {jugador_id}")
    return jugador.to_dict()


def crear_jugador(nombre, fecha_nacimiento=None):
    nombre = _validar_nombre(nombre)
    nuevo_id = jugador_repository.crear(nombre, fecha_nacimiento)
    return obtener_jugador(nuevo_id)


def actualizar_jugador(jugador_id, nombre, fecha_nacimiento=None):
    nombre = _validar_nombre(nombre)
    if not jugador_repository.actualizar(jugador_id, nombre, fecha_nacimiento):
        raise JugadorNoEncontradoError(f"No existe el jugador {jugador_id}")
    return obtener_jugador(jugador_id)


def eliminar_jugador(jugador_id):
    """
    Saca a un jugador del sistema.

    Si nunca jugó, se borra de verdad: no hay historia que preservar y
    dejarlo oculto sería juntar basura.

    Si jugó, se oculta. Borrarlo dejaría partidos con un solo
    participante, y un torneo es un hecho que ocurrió: la final de enero
    la jugaron dos personas, aunque después una se haya ido.

    Devuelve qué se hizo, para que quien llama pueda decirlo.
    """
    if jugador_repository.obtener_por_id(jugador_id) is None:
        raise JugadorNoEncontradoError(f"No existe el jugador {jugador_id}")

    # Ocultar a alguien en medio de un torneo dejaría la pantalla de
    # cargar resultado mostrando un partido contra un fantasma.
    if jugador_repository.esta_en_torneo_sin_terminar(jugador_id):
        raise JugadorInvalidoError(
            "Está participando de un torneo sin terminar. "
            "Terminá ese torneo antes de sacarlo."
        )

    if jugador_repository.tiene_partidos(jugador_id):
        jugador_repository.cambiar_visibilidad(jugador_id, True)
        return "ocultado"

    jugador_repository.eliminar(jugador_id)
    return "eliminado"


def mostrar_jugador(jugador_id):
    """Devuelve a un jugador oculto al sistema."""
    if not jugador_repository.cambiar_visibilidad(jugador_id, False):
        raise JugadorNoEncontradoError(f"No existe el jugador {jugador_id}")


def _validar_nombre(nombre):
    """El nombre es obligatorio y se guarda sin espacios de sobra: así
    'Ana' y 'Ana ' no terminan siendo dos jugadores distintos."""
    if not nombre or not nombre.strip():
        raise JugadorInvalidoError("El nombre del jugador es obligatorio")
    return nombre.strip()
