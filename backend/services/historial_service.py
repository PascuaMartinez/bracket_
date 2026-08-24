"""
Historial global de partidos.

Todos los partidos jugados, de todos los torneos, con filtros. Sirve para
buscar cosas que las estadísticas no responden: qué pasó aquella noche,
cuándo fue la última vez que dos se enfrentaron.
"""
from repositories import partido_repository

# Cuántos se muestran por página. Cincuenta entra cómodo en una pantalla
# sin que la página tarde, y es suficiente para recorrer un torneo entero
# de un tirón.
POR_PAGINA = 50


def buscar(jugador_id=None, torneo_id=None, peleador_id=None, pagina=1):
    pagina = max(1, pagina)
    partidos, total = partido_repository.buscar(
        jugador_id=jugador_id, torneo_id=torneo_id, peleador_id=peleador_id,
        limite=POR_PAGINA, desplazamiento=(pagina - 1) * POR_PAGINA,
    )

    return {
        "partidos": [_presentar(p) for p in partidos],
        "total": total,
        "pagina": pagina,
        "paginas": max(1, -(-total // POR_PAGINA)),   # división redondeada hacia arriba
    }


def _presentar(fila):
    """
    Arma cada partido con los nombres ya resueltos y el ganador
    identificado, para que quien lo muestre no tenga que compararlo.
    """
    gano_el_primero = fila["ganador_id"] == fila["jugador1_id"]
    return {
        "id": fila["id"],
        "torneo_id": fila["torneo_id"],
        "torneo_nombre": fila["torneo_nombre"],
        "fecha": fila["torneo_fecha"].isoformat() if fila["torneo_fecha"] else None,
        "jugador1": {
            "id": fila["jugador1_id"], "nombre": fila["jugador1_nombre"],
            "peleador": fila["peleador1_nombre"], "gano": gano_el_primero,
        },
        "jugador2": {
            "id": fila["jugador2_id"], "nombre": fila["jugador2_nombre"],
            "peleador": fila["peleador2_nombre"], "gano": not gano_el_primero,
        },
        "rondas": fila["rondas_jugadas"],
    }
