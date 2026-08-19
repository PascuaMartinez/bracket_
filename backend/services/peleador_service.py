"""
Reglas de negocio de personajes.

La diferencia con jugadores: el nombre es único. Dos jugadores pueden
llamarse igual (son personas distintas con el mismo nombre), pero dos
personajes con el mismo nombre son el mismo personaje cargado dos veces
-- y eso partiría las estadísticas en dos mitades que no se suman.
"""
from repositories import peleador_repository


class PeleadorNoEncontradoError(Exception):
    pass


class PeleadorInvalidoError(Exception):
    pass


def listar_peleadores():
    return [p.to_dict() for p in peleador_repository.obtener_todos()]


def obtener_peleador(peleador_id):
    peleador = peleador_repository.obtener_por_id(peleador_id)
    if peleador is None:
        raise PeleadorNoEncontradoError(f"No existe el peleador {peleador_id}")
    return peleador.to_dict()


def crear_peleador(nombre):
    nombre = _validar_nombre(nombre)
    _verificar_no_duplicado(nombre)
    nuevo_id = peleador_repository.crear(nombre)
    return obtener_peleador(nuevo_id)


def actualizar_peleador(peleador_id, nombre):
    nombre = _validar_nombre(nombre)
    _verificar_no_duplicado(nombre, excepto_id=peleador_id)
    if not peleador_repository.actualizar(peleador_id, nombre):
        raise PeleadorNoEncontradoError(f"No existe el peleador {peleador_id}")
    return obtener_peleador(peleador_id)


def eliminar_peleador(peleador_id):
    if not peleador_repository.eliminar(peleador_id):
        raise PeleadorNoEncontradoError(f"No existe el peleador {peleador_id}")


def _validar_nombre(nombre):
    if not nombre or not nombre.strip():
        raise PeleadorInvalidoError("El nombre del peleador es obligatorio")
    return nombre.strip()


def _verificar_no_duplicado(nombre, excepto_id=None):
    """excepto_id existe para el caso de editar: al guardar un personaje
    sin cambiarle el nombre, se encontraría a sí mismo como duplicado."""
    existente = peleador_repository.obtener_por_nombre(nombre)
    if existente is not None and existente.id != excepto_id:
        raise PeleadorInvalidoError(f"Ya existe un peleador llamado '{nombre}'")
