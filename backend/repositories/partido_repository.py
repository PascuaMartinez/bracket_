"""Acceso a datos de partidos."""
from database.db import get_connection
from models.partido import Partido


def crear_muchos(partidos, con_ronda=False):
    """Inserta varios partidos de una vez.

    Una sola consulta con todos en vez de una por partido: con 10
    jugadores son 45 enfrentamientos, y 45 idas y vueltas a la base para
    algo que se puede hacer en una no tiene sentido."""
    if not partidos:
        return
    columnas = "torneo_id, jugador1_id, jugador2_id, orden, jornada"
    valores = "%(torneo_id)s, %(jugador1_id)s, %(jugador2_id)s, %(orden)s, %(jornada)s"
    if con_ronda:
        columnas += ", ronda, es_pase_libre, ganador_id, estado"
        valores += ", %(ronda)s, %(es_pase_libre)s, %(ganador_id)s, %(estado)s"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        f"INSERT INTO partido ({columnas}) VALUES ({valores})",
        partidos,
    )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_por_torneo(torneo_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM partido WHERE torneo_id = %s ORDER BY orden ASC", (torneo_id,)
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [Partido.from_row(f) for f in filas]


def obtener_por_id(partido_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM partido WHERE id = %s", (partido_id,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    return Partido.from_row(fila) if fila else None


def obtener_siguiente_pendiente(torneo_id):
    """El próximo partido a jugar, en el orden del fixture."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM partido
           WHERE torneo_id = %s AND estado = 'pendiente'
           ORDER BY orden ASC LIMIT 1""",
        (torneo_id,),
    )
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    return Partido.from_row(fila) if fila else None


def registrar_resultado(partido_id, ganador_id, peleador1_id=None,
                        peleador2_id=None, rondas_jugadas=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE partido
           SET ganador_id = %s, jugador1_peleador_id = %s, jugador2_peleador_id = %s,
               rondas_jugadas = %s, estado = 'finalizado', fecha_jugado = NOW()
           WHERE id = %s""",
        (ganador_id, peleador1_id, peleador2_id, rondas_jugadas, partido_id),
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0


def quedan_pendientes(torneo_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM partido WHERE torneo_id = %s AND estado <> 'finalizado'",
        (torneo_id,),
    )
    cantidad = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return cantidad > 0


def obtener_por_ronda(torneo_id, ronda):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM partido WHERE torneo_id = %s AND ronda = %s
           ORDER BY orden ASC""",
        (torneo_id, ronda),
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [Partido.from_row(f) for f in filas]


def obtener_max_orden(torneo_id):
    """El orden más alto usado hasta ahora, para seguir numerando cuando
    se generan partidos nuevos sobre la marcha."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(MAX(orden), 0) FROM partido WHERE torneo_id = %s", (torneo_id,)
    )
    maximo = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return maximo


def obtener_de_varios_torneos(torneos_ids):
    """
    Los partidos de varios torneos en una sola consulta.

    Devuelve {torneo_id: [partidos]}. Existe para no pedir los partidos
    torneo por torneo cuando hay que recorrerlos todos: con 20 torneos,
    eso es la diferencia entre 20 idas a la base y una.
    """
    if not torneos_ids:
        return {}
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    marcadores = ",".join(["%s"] * len(torneos_ids))
    cursor.execute(
        f"SELECT * FROM partido WHERE torneo_id IN ({marcadores}) ORDER BY orden ASC",
        list(torneos_ids),
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()

    por_torneo = {torneo_id: [] for torneo_id in torneos_ids}
    for fila in filas:
        por_torneo[fila["torneo_id"]].append(Partido.from_row(fila))
    return por_torneo


def cambiar_estado(partido_id, estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE partido SET estado = %s WHERE id = %s", (estado, partido_id)
    )
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas > 0


def obtener_pospuestos(torneo_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM partido WHERE torneo_id = %s AND estado = 'pospuesto'
           ORDER BY orden ASC""",
        (torneo_id,),
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [Partido.from_row(f) for f in filas]
