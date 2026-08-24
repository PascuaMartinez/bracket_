"""Configuración, tal como la necesitan las pantallas."""
from services import api


def obtener():
    return api.get("/configuracion")


def actualizar(datos):
    return api.put("/configuracion", datos)


def listar_estadisticas():
    return api.get("/configuracion/estadisticas")


def guardar_estadisticas_ocultas(ocultas):
    return api.put("/configuracion/estadisticas", {"ocultas": ocultas})
