"""
Acceso a datos de jugadores.

Los repositorios son la única capa que escribe SQL. El resto del proyecto
pide "traeme los jugadores" y no sabe si abajo hay MySQL, otro motor o un
archivo. Eso permite dos cosas concretas: cambiar cómo se guardan los
datos sin tocar la lógica del negocio, y probar esa lógica sustituyendo
el repositorio por uno falso, sin levantar una base.

La regla de la capa: acá no hay decisiones del negocio. Un repositorio
guarda, trae y borra; si algo hay que validar o calcular, va en el
servicio que lo llama.
"""
from database.db import get_connection
from models.jugador import Jugador


def obtener_todos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Ordenado por nombre desde la consulta y no en Python: la base lo
    # hace mejor, y así todas las pantallas muestran el mismo orden sin
    # tener que acordarse de ordenar.
    cursor.execute("SELECT * FROM jugador ORDER BY nombre ASC")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [Jugador.from_row(f) for f in filas]


def obtener_por_id(jugador_id):
    """Devuelve None si no existe. Que el llamador decida qué significa
    eso: para una pantalla de detalle es un 404, y para una validación
    puede ser simplemente un dato más."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jugador WHERE id = %s", (jugador_id,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    return Jugador.from_row(fila) if fila else None


def crear(nombre, fecha_nacimiento=None):
    conn = get_connection()
    cursor = conn.cursor()
    # Los valores van como parámetros (%s) y nunca concatenados al texto
    # de la consulta: es lo que evita la inyección de SQL.
    cursor.execute(
        "INSERT INTO jugador (nombre, fecha_nacimiento) VALUES (%s, %s)",
        (nombre, fecha_nacimiento),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return nuevo_id


def actualizar(jugador_id, nombre, fecha_nacimiento=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE jugador SET nombre = %s, fecha_nacimiento = %s WHERE id = %s",
        (nombre, fecha_nacimiento, jugador_id),
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0


def eliminar(jugador_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jugador WHERE id = %s", (jugador_id,))
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0
