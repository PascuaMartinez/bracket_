"""
Reglas de negocio de partidos.

Dos responsabilidades: armar el fixture cuando arranca un torneo, y
registrar resultados a medida que se juegan.
"""
from repositories import (
    grupo_repository, partido_repository, torneo_repository, vidas_repository,
)
from services import bracket_service, fixture_service, grupos_service


class PartidoNoEncontradoError(Exception):
    pass


class ResultadoInvalidoError(Exception):
    pass


def generar_fixture(torneo_id, modo, jugadores_ids, vidas_iniciales=None,
                    cantidad_grupos=None):
    """
    Arma los partidos iniciales del torneo y lo pasa a 'en curso'.

    Cuánto se puede generar de antemano depende del formato, y esa es la
    diferencia de fondo entre los dos:

    - En todos contra todos se sabe desde el arranque quién juega contra
      quién, así que se genera el fixture completo. Eso permite mostrar
      todo lo que falta y estimar cuánto queda.

    - En eliminación solo se puede armar la primera ronda: quién juega en
      la segunda depende de quién gane en la primera. El resto se va
      generando a medida que se cargan resultados.
    """
    if modo == "eliminacion":
        return _generar_eliminacion(torneo_id, jugadores_ids)
    if modo == "rey_de_la_cancha":
        return _generar_rey_de_la_cancha(torneo_id, jugadores_ids, vidas_iniciales)
    if modo == "grupos_eliminacion":
        return _generar_grupos(torneo_id, jugadores_ids, cantidad_grupos)
    return _generar_todos_contra_todos(torneo_id, jugadores_ids)


def _generar_todos_contra_todos(torneo_id, jugadores_ids):
    jornadas = fixture_service.fixture_round_robin(jugadores_ids)

    partidos = []
    orden = 1
    for numero_jornada, jornada in enumerate(jornadas, start=1):
        for jugador1, jugador2 in jornada:
            partidos.append({
                "torneo_id": torneo_id,
                "jugador1_id": jugador1,
                "jugador2_id": jugador2,
                "orden": orden,
                "jornada": numero_jornada,
            })
            orden += 1

    partido_repository.crear_muchos(partidos)
    torneo_repository.cambiar_estado(torneo_id, "en_curso")
    return len(partidos)


def listar_partidos(torneo_id):
    return [p.to_dict() for p in partido_repository.obtener_por_torneo(torneo_id)]


def obtener_partido_actual(torneo_id):
    """El próximo partido a jugar, o None si ya se jugaron todos.

    Los pospuestos quedan fuera de esta cuenta: se saltean hasta que
    alguien los retome a mano."""
    partido = partido_repository.obtener_siguiente_pendiente(torneo_id)
    return partido.to_dict() if partido else None


def listar_pospuestos(torneo_id):
    return [p.to_dict() for p in partido_repository.obtener_pospuestos(torneo_id)]


def posponer(partido_id):
    """
    Saltea un partido y sigue con el próximo.

    En un torneo real pasa: alguien salió a comprar, se cortó la luz, hay
    que esperar a que llegue uno. Frenar el torneo entero por eso no tiene
    sentido, y cargar un resultado falso para destrabarlo arruinaría las
    estadísticas.

    El partido no se pierde: queda aparte, listo para retomarse.
    """
    partido = partido_repository.obtener_por_id(partido_id)
    if partido is None:
        raise PartidoNoEncontradoError(f"No existe el partido {partido_id}")

    if partido.estado == "finalizado":
        raise ResultadoInvalidoError("Un partido ya jugado no se puede posponer")

    partido_repository.cambiar_estado(partido_id, "pospuesto")


def retomar(partido_id):
    """Devuelve un partido pospuesto a la cola.

    Vuelve a su lugar original según el orden del fixture, no al final:
    el orden dice cómo se dio el torneo, y moverlo distorsionaría eso.
    """
    partido = partido_repository.obtener_por_id(partido_id)
    if partido is None:
        raise PartidoNoEncontradoError(f"No existe el partido {partido_id}")

    if partido.estado != "pospuesto":
        raise ResultadoInvalidoError("Ese partido no está pospuesto")

    partido_repository.cambiar_estado(partido_id, "pendiente")


def cargar_resultado(partido_id, ganador_id, peleador1_id=None,
                     peleador2_id=None, rondas_jugadas=None):
    """
    Registra quién ganó un partido.

    Los personajes y las rondas son opcionales: en un torneo en vivo se
    cargan si hay tiempo, y las estadísticas que dependen de ellos
    simplemente no aparecen cuando faltan. Obligarlos haría que cargar un
    resultado sea más lento que jugar el partido.
    """
    partido = partido_repository.obtener_por_id(partido_id)
    if partido is None:
        raise PartidoNoEncontradoError(f"No existe el partido {partido_id}")

    # El ganador tiene que ser uno de los dos que jugaron. Sin esta
    # validación, un id equivocado dejaría un partido con un ganador que
    # ni siquiera participó, y eso rompería las estadísticas en silencio.
    if ganador_id not in (partido.jugador1_id, partido.jugador2_id):
        raise ResultadoInvalidoError(
            "El ganador tiene que ser uno de los dos jugadores del partido"
        )

    if rondas_jugadas is not None and rondas_jugadas not in (2, 3):
        raise ResultadoInvalidoError(
            "Las rondas jugadas solo pueden ser 2 (barrida) o 3 (cerrado)"
        )

    # registrar_resultado lo deja finalizado, así que un partido pospuesto
    # se destraba solo al cargarle el resultado: no hace falta retomarlo
    # primero.
    partido_repository.registrar_resultado(
        partido_id, ganador_id, peleador1_id, peleador2_id, rondas_jugadas
    )

    # Cada formato avanza distinto. Se hace acá y no en un paso aparte
    # para que el torneo progrese solo a medida que se cargan resultados,
    # sin que nadie tenga que pedirlo.
    torneo = torneo_repository.obtener_por_id(partido.torneo_id)
    if torneo.modo == "rey_de_la_cancha":
        _avanzar_cola(partido, ganador_id)
    elif torneo.modo == "grupos_eliminacion":
        _avanzar_grupos_eliminacion(torneo, partido)
    elif partido.ronda is not None:
        _avanzar_bracket(partido.torneo_id, partido.ronda)

    # Cuando no queda ningún partido pendiente, el torneo terminó. Se
    # decide acá y no desde afuera para que nadie tenga que acordarse de
    # cerrar el torneo a mano.
    if not partido_repository.quedan_pendientes(partido.torneo_id):
        torneo_repository.cambiar_estado(partido.torneo_id, "finalizado")

    return partido_repository.obtener_por_id(partido_id).to_dict()


def _generar_eliminacion(torneo_id, jugadores_ids):
    """Crea solo la primera ronda del cuadro."""
    cruces = bracket_service.sembrar_primera_ronda(jugadores_ids)

    partidos = []
    orden = 1
    for jugador1, jugador2 in cruces:
        # Los pases libres se guardan como partido igual, marcados y ya
        # finalizados. Podrían no guardarse -- no se juegan -- pero
        # entonces habría que llevar en otro lado la lista de quiénes
        # pasaron, y el avance del cuadro tendría dos fuentes de verdad.
        # Así tiene una sola: los partidos de la ronda.
        es_pase_libre = jugador2 is None
        partidos.append({
            "torneo_id": torneo_id,
            "jugador1_id": jugador1,
            "jugador2_id": jugador2,
            "orden": orden,
            "jornada": None,
            "ronda": 1,
            "es_pase_libre": es_pase_libre,
            # El que pasa libre es su propio ganador: no hay nada que
            # cargar y la ronda no debería quedar esperándolo.
            "ganador_id": jugador1 if es_pase_libre else None,
            "estado": "finalizado" if es_pase_libre else "pendiente",
        })
        orden += 1

    partido_repository.crear_muchos(partidos, con_ronda=True)
    torneo_repository.cambiar_estado(torneo_id, "en_curso")
    return sum(1 for p in partidos if not p["es_pase_libre"])


def _avanzar_bracket(torneo_id, ronda):
    """Si la ronda terminó, genera la siguiente con los ganadores."""
    partidos_ronda = partido_repository.obtener_por_ronda(torneo_id, ronda)
    if any(p.estado != "finalizado" for p in partidos_ronda):
        return  # todavía falta jugar alguno

    # Los pases libres ya están entre estos partidos, con su ganador
    # cargado: no hay que buscarlos aparte. Y como vienen ordenados por
    # el orden del cuadro, los mejor sembrados quedan adelante y mantienen
    # la ventaja de su siembra.
    ganadores = [p.ganador_id for p in partidos_ronda]

    if len(ganadores) <= 1:
        return  # ya hay campeón, no hay ronda siguiente

    orden = partido_repository.obtener_max_orden(torneo_id)
    partidos = []
    for i in range(0, len(ganadores), 2):
        orden += 1
        partidos.append({
            "torneo_id": torneo_id,
            "jugador1_id": ganadores[i],
            "jugador2_id": ganadores[i + 1],
            "orden": orden,
            "jornada": None,
            "ronda": ronda + 1,
            "es_pase_libre": False,
            "ganador_id": None,
            "estado": "pendiente",
        })
    partido_repository.crear_muchos(partidos, con_ronda=True)


def _generar_rey_de_la_cancha(torneo_id, jugadores_ids, vidas_iniciales):
    """
    Arranca la cola y crea el primer partido.

    Acá no hay fixture que generar: el próximo cruce depende de quién gane
    el anterior, así que solo se puede saber uno a la vez. Es el formato
    donde menos se puede planificar de antemano -- ni siquiera se sabe
    cuántos partidos va a tener el torneo.
    """
    vidas_repository.inicializar(torneo_id, jugadores_ids, vidas_iniciales)

    partido_repository.crear_muchos([{
        "torneo_id": torneo_id,
        "jugador1_id": jugadores_ids[0],
        "jugador2_id": jugadores_ids[1],
        "orden": 1,
        "jornada": None,
        "ronda": None,
        "es_pase_libre": False,
        "ganador_id": None,
        "estado": "pendiente",
    }], con_ronda=True)

    torneo_repository.cambiar_estado(torneo_id, "en_curso")
    return 1


def _avanzar_cola(partido, ganador_id):
    """
    Resuelve qué pasa después de un partido: el perdedor pierde una vida,
    el ganador se queda en cancha, y entra el próximo de la cola.
    """
    torneo_id = partido.torneo_id
    perdedor_id = (
        partido.jugador2_id if ganador_id == partido.jugador1_id
        else partido.jugador1_id
    )

    vidas_restantes = vidas_repository.descontar_vida(torneo_id, perdedor_id)

    estado = vidas_repository.obtener_estado(torneo_id)

    if vidas_restantes <= 0:
        # El orden de eliminación se numera al caer y no se recalcula
        # después: es el dato que dice quién aguantó más.
        orden = vidas_repository.contar_eliminados(torneo_id) + 1
        vidas_repository.eliminar(torneo_id, perdedor_id, orden)
    else:
        # Vuelve al final: la posición más alta que haya, más uno.
        ultima = max((j["posicion_cola"] or 0) for j in estado)
        vidas_repository.mandar_al_final_de_la_cola(torneo_id, perdedor_id, ultima + 1)

    vidas_repository.poner_en_cancha(torneo_id, ganador_id)

    # Se relee el estado: acaba de cambiar y decidir sobre el anterior
    # dejaría al eliminado todavía como candidato a entrar.
    estado = vidas_repository.obtener_estado(torneo_id)
    en_pie = [j for j in estado if not j["eliminado"]]

    if len(en_pie) <= 1:
        torneo_repository.cambiar_estado(torneo_id, "finalizado")
        return

    desafiante = _proximo_en_la_cola(estado, ganador_id)
    if desafiante is None:
        return

    partido_repository.crear_muchos([{
        "torneo_id": torneo_id,
        "jugador1_id": ganador_id,
        "jugador2_id": desafiante["jugador_id"],
        "orden": partido_repository.obtener_max_orden(torneo_id) + 1,
        "jornada": None,
        "ronda": None,
        "es_pase_libre": False,
        "ganador_id": None,
        "estado": "pendiente",
    }], con_ronda=True)


def _proximo_en_la_cola(estado, en_cancha_id):
    """El primero de la fila que no esté eliminado ni sea el que ya está
    en cancha."""
    esperando = [
        j for j in estado
        if not j["eliminado"] and j["jugador_id"] != en_cancha_id
    ]
    if not esperando:
        return None
    return min(esperando, key=lambda j: j["posicion_cola"] or 0)


def _generar_grupos(torneo_id, jugadores_ids, cantidad_grupos):
    """
    Arma los grupos y todos sus partidos.

    Dentro de cada grupo se juega todos contra todos, así que el fixture
    de la fase de grupos sale completo. El cuadro de eliminación no: quién
    lo juega depende de quién clasifique.
    """
    repartidos = grupos_service.repartir_en_grupos(jugadores_ids, cantidad_grupos)

    partidos = []
    orden = 1
    for indice, jugadores_del_grupo in enumerate(repartidos):
        grupo_id = grupo_repository.crear(
            torneo_id, grupos_service.nombre_de_grupo(indice)
        )
        grupo_repository.asignar_jugadores(torneo_id, grupo_id, jugadores_del_grupo)

        for jornada in fixture_service.fixture_round_robin(jugadores_del_grupo):
            for jugador1, jugador2 in jornada:
                partidos.append({
                    "torneo_id": torneo_id,
                    "jugador1_id": jugador1,
                    "jugador2_id": jugador2,
                    "orden": orden,
                    "jornada": None,
                    # ronda None marca que es de la fase de grupos; el
                    # cuadro usa ronda 1, 2, 3...
                    "ronda": None,
                    "es_pase_libre": False,
                    "ganador_id": None,
                    "estado": "pendiente",
                })
                orden += 1

    partido_repository.crear_muchos(partidos, con_ronda=True)
    torneo_repository.cambiar_estado(torneo_id, "en_curso")
    return len(partidos)


def _avanzar_grupos_eliminacion(torneo, partido):
    """
    Decide qué hacer después de un partido: si fue de grupos y ya
    terminaron todos, calcula clasificados y arranca el cuadro. Si fue del
    cuadro, avanza la ronda.
    """
    if partido.ronda is not None:
        _avanzar_bracket(torneo.id, partido.ronda)
        return

    # Los grupos terminan en momentos distintos, y el cuadro no puede
    # arrancar hasta que terminen TODOS: sembrar con la mitad de los
    # clasificados armaría un cuadro incompleto.
    if _quedan_partidos_de_grupos(torneo.id):
        return

    _cerrar_fase_de_grupos(torneo)


def _quedan_partidos_de_grupos(torneo_id):
    return any(
        p.ronda is None and p.estado != "finalizado"
        for p in partido_repository.obtener_por_torneo(torneo_id)
    )


def _cerrar_fase_de_grupos(torneo):
    """Calcula quién clasifica de cada grupo y genera la primera ronda."""
    from services import tabla_service

    grupos = grupo_repository.obtener_por_torneo(torneo.id)
    tamanos = [len(grupo_repository.obtener_jugadores(g["id"])) for g in grupos]
    cupos = grupos_service.repartir_cupos(torneo.cupos_eliminacion, tamanos)

    clasificados = []
    hubo_empate = False

    for grupo, cupos_del_grupo in zip(grupos, cupos):
        tabla = tabla_service.calcular_tabla_de_grupo(torneo.id, grupo["id"])

        empate = grupos_service.detectar_empate_en_el_corte(tabla, cupos_del_grupo)
        if empate is not None:
            # No se resuelve solo. Desempatar por win rate o por orden
            # alfabético sería decidir con un criterio que el torneo nunca
            # jugó: los empatados hicieron exactamente lo mismo. Se deja
            # sin marcar y el organizador decide -- jugando un desempate o
            # a dedo.
            hubo_empate = True
            decididos = [f["jugador_id"] for f in tabla
                         if f["puntos"] > empate["empatados"][0]["puntos"]]
            grupo_repository.marcar_clasificados(grupo["id"], decididos)
            continue

        pasan = [f["jugador_id"] for f in tabla[:cupos_del_grupo]]
        grupo_repository.marcar_clasificados(grupo["id"], pasan)
        clasificados.append(pasan)

    # Con algún empate sin resolver no se puede sembrar: falta saber
    # quiénes juegan el cuadro.
    if hubo_empate:
        return

    _sembrar_cuadro(torneo)


def _intercalar(listas):
    """Toma el primero de cada lista, después el segundo de cada una, etc.

    Es lo que evita que dos primeros de grupo se enfrenten de entrada: al
    intercalar, quedan en extremos opuestos del cuadro."""
    resultado = []
    for posicion in range(max((len(l) for l in listas), default=0)):
        for lista in listas:
            if posicion < len(lista):
                resultado.append(lista[posicion])
    return resultado


def resolver_empate(torneo_id, grupo_id, jugador_id, clasifica, observacion=None):
    """
    Decide a mano si alguien clasifica.

    Se usa cuando quedó un empate en el corte: el organizador resuelve
    -- porque jugaron un desempate aparte, porque uno se fue, por lo que
    sea -- y el sistema toma esa decisión como válida.

    Queda marcado como forzado y con una observación. Un clasificado
    decidido a dedo dice algo distinto de uno que ganó su lugar en la
    cancha, y esa diferencia tiene que poder verse después.
    """
    grupo_repository.forzar_clasificado(grupo_id, jugador_id, clasifica, observacion)

    # Si con esto ya no queda nadie sin resolver, el cuadro puede arrancar.
    if not grupo_repository.hay_indecisos(torneo_id):
        torneo = torneo_repository.obtener_por_id(torneo_id)
        _sembrar_cuadro(torneo)


def _sembrar_cuadro(torneo):
    """Arma la primera ronda del cuadro con los que clasificaron."""
    clasificados_por_grupo = {}
    for fila in grupo_repository.obtener_clasificados(torneo.id):
        clasificados_por_grupo.setdefault(fila["grupo_id"], []).append(fila["jugador_id"])

    sembrados = _intercalar(list(clasificados_por_grupo.values()))
    if len(sembrados) < 2:
        return

    cruces = bracket_service.sembrar_primera_ronda(sembrados)
    orden = partido_repository.obtener_max_orden(torneo.id)
    partidos = []
    for jugador1, jugador2 in cruces:
        orden += 1
        es_pase_libre = jugador2 is None
        partidos.append({
            "torneo_id": torneo.id, "jugador1_id": jugador1, "jugador2_id": jugador2,
            "orden": orden, "jornada": None, "ronda": 1,
            "es_pase_libre": es_pase_libre,
            "ganador_id": jugador1 if es_pase_libre else None,
            "estado": "finalizado" if es_pase_libre else "pendiente",
        })
    partido_repository.crear_muchos(partidos, con_ronda=True)
