"""
Conexión a MySQL.

Un único lugar que sabe cómo conectarse: el resto del proyecto pide una
conexión con get_connection() y no conoce credenciales ni detalles del
driver. Si mañana cambia algo de cómo se conecta (un pool, un timeout,
otro motor), se cambia acá y nada más.
"""
import mysql.connector
from mysql.connector import Error

from config import Config


def _config():
    return {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "database": Config.DB_NAME,
    }


def get_connection():
    """
    Devuelve una conexión lista para usar.

    El error del driver se envuelve en uno propio: quien llama no tiene
    por qué saber que abajo hay mysql.connector, y así el día que cambie
    el driver no hay que tocar los except de todo el proyecto.
    """
    try:
        return mysql.connector.connect(**_config())
    except Error as e:
        raise RuntimeError(f"No se pudo conectar a la base de datos: {e}")
