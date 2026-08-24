"""Acceso a datos de grupos."""
from database.db import get_connection


def crear(torneo_id, nombre):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO grupo (torneo_id, nombre) VALUES (%s, %s)", (torneo_id, nombre)
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return nuevo_id


def obtener_por_torneo(torneo_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM grupo WHERE torneo_id = %s ORDER BY id ASC", (torneo_id,)
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return filas


def asignar_jugadores(torneo_id, grupo_id, jugadores_ids):
    conn = get_connection()
    cursor = conn.cursor()
    for jugador_id in jugadores_ids:
        cursor.execute(
            "SELECT id FROM torneo_jugador WHERE torneo_id = %s AND jugador_id = %s",
            (torneo_id, jugador_id),
        )
        torneo_jugador_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO torneo_jugador_grupo (torneo_jugador_id, grupo_id) VALUES (%s, %s)",
            (torneo_jugador_id, grupo_id),
        )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_jugadores(grupo_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT tj.jugador_id, j.nombre, tjg.clasificado
           FROM torneo_jugador_grupo tjg
           JOIN torneo_jugador tj ON tj.id = tjg.torneo_jugador_id
           JOIN jugador j ON j.id = tj.jugador_id
           WHERE tjg.grupo_id = %s
           ORDER BY j.nombre ASC""",
        (grupo_id,),
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return filas


def marcar_clasificados(grupo_id, jugadores_ids_que_clasifican):
    """Marca quién pasó y quién no. Se marcan TODOS y no solo los que
    pasan, para poder distinguir 'no clasificó' de 'todavía no se sabe'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE torneo_jugador_grupo tjg
           JOIN torneo_jugador tj ON tj.id = tjg.torneo_jugador_id
           SET tjg.clasificado = (tj.jugador_id IN (%s))
           WHERE tjg.grupo_id = %%s"""
        % ",".join(["%s"] * len(jugadores_ids_que_clasifican) or ["NULL"]),
        (*jugadores_ids_que_clasifican, grupo_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_clasificados(torneo_id):
    """Los que pasaron a la eliminación, en orden de grupo y puesto."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT tj.jugador_id, g.id AS grupo_id
           FROM torneo_jugador_grupo tjg
           JOIN torneo_jugador tj ON tj.id = tjg.torneo_jugador_id
           JOIN grupo g ON g.id = tjg.grupo_id
           WHERE g.torneo_id = %s AND tjg.clasificado = TRUE
           ORDER BY g.id ASC""",
        (torneo_id,),
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return filas


def forzar_clasificado(grupo_id, jugador_id, clasifica, observacion=None):
    """Decide a mano si alguien pasa, y deja anotado el motivo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE torneo_jugador_grupo tjg
           JOIN torneo_jugador tj ON tj.id = tjg.torneo_jugador_id
           SET tjg.clasificado = %s, tjg.clasificacion_forzada = TRUE,
               tjg.observacion = %s
           WHERE tjg.grupo_id = %s AND tj.jugador_id = %s""",
        (clasifica, observacion, grupo_id, jugador_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


def hay_indecisos(torneo_id):
    """Si queda alguien sin resolver: la fase de grupos terminó pero su
    clasificación sigue en NULL, esperando que se decida el empate."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COUNT(*) FROM torneo_jugador_grupo tjg
           JOIN grupo g ON g.id = tjg.grupo_id
           WHERE g.torneo_id = %s AND tjg.clasificado IS NULL""",
        (torneo_id,),
    )
    cantidad = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return cantidad > 0
