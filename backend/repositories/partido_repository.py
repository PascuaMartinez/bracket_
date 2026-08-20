"""Acceso a datos de partidos."""
from database.db import get_connection
from models.partido import Partido


def crear_muchos(partidos):
    """Inserta el fixture completo de una vez.

    Una sola consulta con todos los partidos en vez de una por partido:
    con 10 jugadores son 45 enfrentamientos, y 45 idas y vueltas a la base
    para algo que se puede hacer en una no tiene sentido."""
    if not partidos:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """INSERT INTO partido (torneo_id, jugador1_id, jugador2_id, orden, jornada)
           VALUES (%(torneo_id)s, %(jugador1_id)s, %(jugador2_id)s, %(orden)s, %(jornada)s)""",
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
