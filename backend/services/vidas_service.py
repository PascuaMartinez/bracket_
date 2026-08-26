"""Vidas restantes en los formatos que las usan."""
from repositories import vidas_repository


def vidas_de(torneo, jugadores_ids):
    """
    Cuántas vidas le quedan a cada uno.

    Devuelve un diccionario vacío en los formatos que no usan vidas: así
    quien lo muestra pregunta una sola cosa -- si hay dato -- en vez de
    tener que saber qué formatos las tienen.
    """
    if torneo is None or torneo.modo != "rey_de_la_cancha":
        return {}

    estado = {j["jugador_id"]: j["vidas"]
              for j in vidas_repository.obtener_estado(torneo.id)}
    return {jid: estado.get(jid) for jid in jugadores_ids if jid in estado}
