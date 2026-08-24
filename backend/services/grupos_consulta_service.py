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
