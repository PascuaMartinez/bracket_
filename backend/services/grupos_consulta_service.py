"""
Los grupos de un torneo, con su tabla y sus clasificados.

Va aparte del servicio que ARMA los grupos: uno se usa al crear el
torneo y el otro mientras se juega. Mezclarlos haría que cualquier
pantalla que solo quiere mostrar la tabla arrastre también la lógica de
reparto.
"""
from repositories import grupo_repository, partido_repository
from services import tabla_service


def obtener_grupos(torneo_id):
    partidos = partido_repository.obtener_por_torneo(torneo_id)

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

        jugadores_del_grupo = set(clasificados.keys())

        # Los partidos de la fase de grupos propiamente dicha (no el
        # cuadro, no un desempate): si queda alguno sin jugar, el grupo
        # todavía se está disputando y "nadie tiene clasificado asignado
        # todavía" no significa que haya un empate -- significa que
        # todavía no se sabe. Sin este chequeo, un torneo recién creado
        # mostraría a todo el grupo como "en disputa" desde el arranque.
        partidos_de_fase = [
            p for p in partidos
            if p.ronda is None and not p.es_desempate
            and p.jugador1_id in jugadores_del_grupo
        ]
        fase_terminada = bool(partidos_de_fase) and all(
            p.estado == "finalizado" for p in partidos_de_fase
        )

        desempates_del_grupo = [
            p for p in partidos
            if p.es_desempate
            and p.jugador1_id in jugadores_del_grupo
            and p.jugador2_id in jugadores_del_grupo
        ]
        # Si hay un desempate sin terminar, todavía se está jugando: no
        # es el momento de ofrecer forzar un clasificado a mano. Esa
        # opción es para cuando el desempate YA se jugó y no alcanzó
        # -- el triangular perfecto -- no para saltearse la cancha.
        desempate_pendiente = any(p.estado != "finalizado" for p in desempates_del_grupo)

        for fila in tabla:
            fila["clasificado"] = clasificados.get(fila["jugador_id"])
            # Sin resolver: la fase de grupos terminó y quedó un empate en
            # el corte esperando una decisión. Mientras la fase siga en
            # curso, nadie está "sin resolver" -- simplemente todavía no
            # jugó lo suficiente.
            fila["sin_resolver"] = fase_terminada and fila["clasificado"] is None
            # Se ofrece forzar solo cuando no hay nada pendiente de
            # jugarse: si el desempate está en curso, la acción correcta
            # es ir a jugarlo, no forzarlo desde el listado.
            fila["puede_forzarse"] = fila["sin_resolver"] and not desempate_pendiente

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
