"""
Los grupos de un torneo, con su tabla y sus clasificados.

Va aparte del servicio que ARMA los grupos: uno se usa al crear el
torneo y el otro mientras se juega. Mezclarlos haría que cualquier
pantalla que solo quiere mostrar la tabla arrastre también la lógica de
reparto.
"""
from repositories import grupo_repository
from services import tabla_service


def obtener_grupos(torneo_id):
    grupos = []
    for grupo in grupo_repository.obtener_por_torneo(torneo_id):
        tabla = tabla_service.calcular_tabla_de_grupo(torneo_id, grupo["id"])

        # Quién clasificó ya está decidido y guardado: se lo agrega a cada
        # fila para que la pantalla pueda marcarlos sin volver a calcular
        # los cupos.
        clasificados = {
            j["jugador_id"]: j["clasificado"]
            for j in grupo_repository.obtener_jugadores(grupo["id"])
        }
        for fila in tabla:
            # None significa "sin resolver": la fase terminó pero quedó un
            # empate en el corte esperando una decisión. Es distinto de
            # False, que es "no clasificó".
            fila["clasificado"] = clasificados.get(fila["jugador_id"])
            fila["sin_resolver"] = fila["clasificado"] is None

        grupos.append({"id": grupo["id"], "nombre": grupo["nombre"], "tabla": tabla})
    return grupos


def desempeno_de(torneo_id, jugadores_ids):
    """
    Cómo le fue en su grupo a cada uno de los que están en el repechaje.

    En un desempate esto no haría falta: los empatados tienen exactamente
    el mismo registro, por eso empataron. Pero en un repechaje los
    candidatos vienen de grupos distintos y pueden haber llegado ahí de
    formas muy diferentes -- uno con dos victorias y otro con una -- así
    que si hay que decidir a mano, esa información importa.
    """
    from services import tabla_service

    resultado = []
    for grupo in grupo_repository.obtener_por_torneo(torneo_id):
        tabla = tabla_service.calcular_tabla_de_grupo(torneo_id, grupo["id"])
        for fila in tabla:
            if fila["jugador_id"] in jugadores_ids:
                resultado.append({
                    "jugador_id": fila["jugador_id"],
                    "nombre": fila["nombre"],
                    "grupo": grupo["nombre"],
                    "puesto": fila["puesto"],
                    "pj": fila["pj"],
                    "pg": fila["pg"],
                    "pp": fila["pp"],
                    "win_rate": fila["win_rate"],
                })

    # Del que mejor le fue al que peor: si hay que elegir a mano, el orden
    # ya sugiere por dónde empezar a mirar.
    return sorted(resultado, key=lambda f: (-f["pg"], -f["win_rate"]))
