"""Acceso a datos de torneos y de sus participantes."""
from database.db import get_connection
from models.torneo import Torneo


def obtener_todos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Del más reciente al más viejo: es el orden en que se los quiere ver.
    cursor.execute("SELECT * FROM torneo ORDER BY fecha DESC, id DESC")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [Torneo.from_row(f) for f in filas]


def obtener_por_id(torneo_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM torneo WHERE id = %s", (torneo_id,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    return Torneo.from_row(fila) if fila else None


def existe_sin_finalizar():
    """Si hay algún torneo que todavía no terminó. La app está pensada
    para acompañar un torneo mientras se juega, y dos en paralelo harían
    ambiguo a cuál se le está cargando cada resultado."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM torneo WHERE estado <> 'finalizado'")
    cantidad = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return cantidad > 0


def crear(nombre, modo, fecha, descripcion=None, lugar=None, vidas_iniciales=None,
          cupos_eliminacion=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO torneo (nombre, modo, fecha, descripcion, lugar,
                              vidas_iniciales, cupos_eliminacion, estado)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 'planificado')""",
        (nombre, modo, fecha, descripcion, lugar, vidas_iniciales, cupos_eliminacion),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return nuevo_id


def actualizar(torneo_id, nombre, fecha, descripcion=None, lugar=None):
    """Solo los datos descriptivos. El modo NO se edita a propósito:
    cambiarlo con partidos ya jugados dejaría el torneo inconsistente con
    lo que efectivamente pasó."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE torneo SET nombre = %s, fecha = %s, descripcion = %s, lugar = %s
           WHERE id = %s""",
        (nombre, fecha, descripcion, lugar, torneo_id),
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0


def cambiar_estado(torneo_id, estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE torneo SET estado = %s WHERE id = %s", (estado, torneo_id))
    conn.commit()
    cursor.close()
    conn.close()


def eliminar(torneo_id):
    """Borra el torneo y todo lo que cuelga de él.

    El orden importa: las claves foráneas impiden dejar filas apuntando a
    algo que ya no existe, así que se borra de las hojas hacia la raíz.
    Las vidas cuelgan de la participación, la participación del torneo.

    Va todo en una transacción: si fallara a la mitad, el torneo quedaría
    parcialmente borrado -- sin partidos pero todavía en la lista, o al
    revés -- y eso es peor que no haberlo borrado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        cursor.execute(
            """DELETE v FROM torneo_jugador_vidas v
               JOIN torneo_jugador tj ON tj.id = v.torneo_jugador_id
               WHERE tj.torneo_id = %s""",
            (torneo_id,),
        )
        cursor.execute("DELETE FROM partido WHERE torneo_id = %s", (torneo_id,))
        cursor.execute("DELETE FROM torneo_jugador WHERE torneo_id = %s", (torneo_id,))
        cursor.execute("DELETE FROM torneo WHERE id = %s", (torneo_id,))
        filas_afectadas = cursor.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    return filas_afectadas > 0


def inscribir_jugadores(torneo_id, jugadores_ids):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO torneo_jugador (torneo_id, jugador_id) VALUES (%s, %s)",
        [(torneo_id, jid) for jid in jugadores_ids],
    )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_participantes(torneo_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT tj.id AS torneo_jugador_id, j.id AS jugador_id, j.nombre
           FROM torneo_jugador tj
           JOIN jugador j ON j.id = tj.jugador_id
           WHERE tj.torneo_id = %s
           ORDER BY j.nombre ASC""",
        (torneo_id,),
    )
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return filas
