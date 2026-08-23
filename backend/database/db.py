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
from database import medicion


def _config():
    return {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "database": Config.DB_NAME,
    }


class _ConexionMedida:
    """
    Envuelve la conexión para contar las consultas que pasan por ella.

    Va acá y no en cada repositorio: son decenas de funciones, y agregarle
    a cada una una línea de medición sería ruido que además se olvidaría
    en la próxima que se escriba. Envolviendo la conexión, todo lo que
    consulte queda contado sin que nadie tenga que acordarse.
    """

    def __init__(self, conexion):
        self._conexion = conexion

    def cursor(self, *args, **kwargs):
        return _CursorMedido(self._conexion.cursor(*args, **kwargs))

    def __getattr__(self, nombre):
        return getattr(self._conexion, nombre)


class _CursorMedido:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, consulta, *args, **kwargs):
        medicion.registrar(consulta)
        return self._cursor.execute(consulta, *args, **kwargs)

    def executemany(self, consulta, *args, **kwargs):
        medicion.registrar(consulta)
        return self._cursor.executemany(consulta, *args, **kwargs)

    def __getattr__(self, nombre):
        return getattr(self._cursor, nombre)

    def __iter__(self):
        return iter(self._cursor)


def get_connection():
    """
    Devuelve una conexión lista para usar.

    El error del driver se envuelve en uno propio: quien llama no tiene
    por qué saber que abajo hay mysql.connector, y así el día que cambie
    el driver no hay que tocar los except de todo el proyecto.
    """
    try:
        return _ConexionMedida(mysql.connector.connect(**_config()))
    except Error as e:
        raise RuntimeError(f"No se pudo conectar a la base de datos: {e}")
