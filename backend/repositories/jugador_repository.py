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


def obtener_todos(incluir_ocultos=False):
    """Por defecto solo los activos.

    Los ocultos se piden explícitamente: así ninguna pantalla los muestra
    por olvido, que es lo contrario de lo que se busca al ocultar a
    alguien."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Ordenado por nombre desde la consulta y no en Python: la base lo
    # hace mejor, y así todas las pantallas muestran el mismo orden sin
    # tener que acordarse de ordenar.
    filtro = "" if incluir_ocultos else "WHERE oculto = FALSE"
    cursor.execute(f"SELECT * FROM jugador {filtro} ORDER BY nombre ASC")
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


def actualizar_imagen(jugador_id, campo, ruta):
    """Guarda la ruta de una imagen. campo dice cuál de las dos."""
    if campo not in ("imagen_vertical_path", "imagen_icono_path"):
        raise ValueError(f"Campo de imagen desconocido: {campo}")
    conn = get_connection()
    cursor = conn.cursor()
    # El nombre de columna se interpola pero sale de una lista cerrada,
    # nunca de datos del usuario: los valores siguen yendo como parámetros.
    cursor.execute(f"UPDATE jugador SET {campo} = %s WHERE id = %s", (ruta, jugador_id))
    conn.commit()
    cursor.close()
    conn.close()


def cambiar_visibilidad(jugador_id, oculto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE jugador SET oculto = %s WHERE id = %s", (oculto, jugador_id))
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas > 0


def tiene_partidos(jugador_id):
    """Si participó de algún partido. Decide si se puede borrar de verdad
    o hay que ocultarlo para no romper la historia de esos torneos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM partido WHERE jugador1_id = %s OR jugador2_id = %s",
        (jugador_id, jugador_id),
    )
    cantidad = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return cantidad > 0


def esta_en_torneo_sin_terminar(jugador_id):
    """Si participa de un torneo que todavía se está jugando.

    Ocultar a alguien en medio de un torneo dejaría la pantalla de cargar
    resultado mostrando un partido contra un fantasma."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COUNT(*) FROM torneo_jugador tj
           JOIN torneo t ON t.id = tj.torneo_id
           WHERE tj.jugador_id = %s AND t.estado <> 'finalizado'""",
        (jugador_id,),
    )
    cantidad = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return cantidad > 0
