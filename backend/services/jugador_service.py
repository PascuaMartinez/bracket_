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


def listar_jugadores():
    return [j.to_dict() for j in jugador_repository.obtener_todos()]


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
    if not jugador_repository.eliminar(jugador_id):
        raise JugadorNoEncontradoError(f"No existe el jugador {jugador_id}")


def _validar_nombre(nombre):
    """El nombre es obligatorio y se guarda sin espacios de sobra: así
    'Ana' y 'Ana ' no terminan siendo dos jugadores distintos."""
    if not nombre or not nombre.strip():
        raise JugadorInvalidoError("El nombre del jugador es obligatorio")
    return nombre.strip()
