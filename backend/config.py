import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Toda la configuración sale de variables de entorno, sin valores por
    defecto para las credenciales: si falta una, la app falla al conectar
    en vez de arrancar contra una base equivocada en silencio.

    Los valores reales viven en un .env que no se versiona. El
    .env.example de al lado documenta cuáles hacen falta.
    """

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("FLASK_PORT", 5000))
