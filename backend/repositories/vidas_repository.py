"""
Estado de la cola en un torneo de rey de la cancha.

Quién está en cancha, quién espera turno, a quién le quedan vidas.
"""
from database.db import get_connection


def inicializar(torneo_id, jugadores_ids_en_orden, vidas_iniciales):
    """Arranca la cola. El orden de la lista define quién entra primero."""
    conn = get_connection()
    cursor = conn.cursor()
    for posicion, jugador_id in enumerate(jugadores_ids_en_orden):
        cursor.execute(
            "SELECT id FROM torneo_jugador WHERE torneo_id = %s AND jugador_id = %s",
            (torneo_id, jugador_id),
        )
        torneo_jugador_id = cursor.fetchone()[0]
        cursor.execute(
            """INSERT INTO torneo_jugador_vidas
               (torneo_jugador_id, vidas, posicion_cola, en_cancha)
               VALUES (%s, %s, %s, %s)""",
            # Los dos primeros arrancan jugando; el resto espera.
            (torneo_jugador_id, vidas_iniciales, posicion, posicion < 2),
        )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_estado(torneo_id):
    """Todos los jugadores con su estado en la cola."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT tj.jugador_id, j.nombre, v.vidas, v.posicion_cola,
                  v.en_cancha, v.eliminado, v.orden_eliminacion
           FROM torneo_jugador_vidas v
           JOIN torneo_jugador tj ON tj.id = v.torneo_jugador_id
           JOIN jugador j ON j.id = tj.jugador_id
           WHERE tj.torneo_id = %s
           ORDER BY v.posicion_cola ASC""",
        (torneo_id,),
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return filas


def descontar_vida(torneo_id, jugador_id):
    """Le saca una vida y devuelve cuántas le quedan."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE torneo_jugador_vidas v
           JOIN torneo_jugador tj ON tj.id = v.torneo_jugador_id
           SET v.vidas = v.vidas - 1
           WHERE tj.torneo_id = %s AND tj.jugador_id = %s""",
        (torneo_id, jugador_id),
    )
    conn.commit()
    cursor.execute(
        """SELECT v.vidas FROM torneo_jugador_vidas v
           JOIN torneo_jugador tj ON tj.id = v.torneo_jugador_id
           WHERE tj.torneo_id = %s AND tj.jugador_id = %s""",
        (torneo_id, jugador_id),
    )
    vidas = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return vidas


def eliminar(torneo_id, jugador_id, orden_eliminacion):
    _actualizar(torneo_id, jugador_id,
                "v.eliminado = TRUE, v.en_cancha = FALSE, v.orden_eliminacion = %s",
                (orden_eliminacion,))


def mandar_al_final_de_la_cola(torneo_id, jugador_id, nueva_posicion):
    _actualizar(torneo_id, jugador_id,
                "v.posicion_cola = %s, v.en_cancha = FALSE", (nueva_posicion,))


def poner_en_cancha(torneo_id, jugador_id):
    _actualizar(torneo_id, jugador_id, "v.en_cancha = TRUE", ())


def contar_eliminados(torneo_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COUNT(*) FROM torneo_jugador_vidas v
           JOIN torneo_jugador tj ON tj.id = v.torneo_jugador_id
           WHERE tj.torneo_id = %s AND v.eliminado = TRUE""",
        (torneo_id,),
    )
    cantidad = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return cantidad


def _actualizar(torneo_id, jugador_id, asignaciones, params):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""UPDATE torneo_jugador_vidas v
            JOIN torneo_jugador tj ON tj.id = v.torneo_jugador_id
            SET {asignaciones}
            WHERE tj.torneo_id = %s AND tj.jugador_id = %s""",
        (*params, torneo_id, jugador_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
