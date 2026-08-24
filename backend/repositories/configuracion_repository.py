"""Acceso a la configuración del sistema."""
from database.db import get_connection


def obtener():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM configuracion WHERE id = 1")
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    # Si la fila no está -- base recién creada a mano, por ejemplo -- se
    # devuelven los valores por defecto en vez de fallar: la aplicación
    # tiene que poder arrancar igual.
    return fila or {"nombre_club": "Bracket", "texto_inicio": None,
                    "texto_formatos": None}


def actualizar(nombre_club, texto_inicio=None, texto_formatos=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE configuracion
           SET nombre_club = %s, texto_inicio = %s, texto_formatos = %s
           WHERE id = 1""",
        (nombre_club, texto_inicio, texto_formatos),
    )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_ocultas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clave FROM estadistica_oculta")
    claves = {fila[0] for fila in cursor.fetchall()}
    cursor.close()
    conn.close()
    return claves


def guardar_ocultas(claves):
    """Reemplaza la lista entera.

    Se borra y se inserta de nuevo en una transacción, en vez de calcular
    qué cambió: la lista es corta y así no hay forma de que quede a medias
    entre lo viejo y lo nuevo.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        cursor.execute("DELETE FROM estadistica_oculta")
        if claves:
            cursor.executemany(
                "INSERT INTO estadistica_oculta (clave) VALUES (%s)",
                [(clave,) for clave in claves],
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
