"""Acceso a datos de usuarios."""
from database.db import get_connection


def obtener_por_nombre(nombre_usuario):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM usuario WHERE nombre_usuario = %s", (nombre_usuario,)
    )
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    return fila


def crear(nombre_usuario, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuario (nombre_usuario, password_hash) VALUES (%s, %s)",
        (nombre_usuario, password_hash),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return nuevo_id


def contar():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuario")
    cantidad = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return cantidad
