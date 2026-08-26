"""
Datos de torneos, tal como los necesitan las pantallas.

Esta capa existe para que las rutas no tengan que saber qué endpoints
combinar ni cómo se llaman los campos del backend. Una pantalla pide "el
detalle del torneo" y recibe todo junto.
"""
from services import api


def listar():
    return api.get("/torneos")


def obtener(torneo_id):
    return api.get(f"/torneos/{torneo_id}")


def detalle_completo(torneo_id):
    """El torneo con todo lo que la pantalla de detalle necesita.

    Se juntan acá las tres llamadas y no en la plantilla para que la
    pantalla reciba un dato ya armado: si mañana el backend expone todo
    en un solo endpoint, cambia esta función y nada más."""
    return {
        "torneo": obtener(torneo_id),
        "tabla": api.get(f"/torneos/{torneo_id}/tabla"),
        "partidos": api.get(f"/torneos/{torneo_id}/partidos"),
    }


def grupos(torneo_id):
    """Los grupos con su tabla, para el detalle del torneo."""
    return api.get(f"/torneos/{torneo_id}/grupos")


def partido_actual(torneo_id):
    """El próximo partido a jugar, o None si ya se jugaron todos."""
    return api.get(f"/torneos/{torneo_id}/partido-actual")


def pospuestos(torneo_id):
    return api.get(f"/torneos/{torneo_id}/pospuestos")


def posponer(partido_id):
    return api.post(f"/partidos/{partido_id}/posponer", {})


def retomar(partido_id):
    return api.post(f"/partidos/{partido_id}/retomar", {})


def resolver_empate(torneo_id, grupo_id, jugador_id, clasifica, observacion=None):
    return api.post(f"/torneos/{torneo_id}/grupos/{grupo_id}/resolver", {
        "jugador_id": jugador_id,
        "clasifica": clasifica,
        "observacion": observacion,
    })


def corregibles(torneo_id):
    """Los partidos ya jugados que todavía se pueden corregir."""
    return api.get(f"/torneos/{torneo_id}/corregibles")


def corregir_resultado(partido_id, datos):
    return api.put(f"/partidos/{partido_id}/resultado", datos)


def crear(datos):
    return api.post("/torneos", datos)


def actualizar(torneo_id, datos):
    return api.put(f"/torneos/{torneo_id}", datos)


def eliminar(torneo_id):
    return api.delete(f"/torneos/{torneo_id}")


def cargar_resultado(partido_id, datos):
    return api.post(f"/partidos/{partido_id}/resultado", datos)


def tabla_historica():
    return api.get("/torneos/tabla-historica")
