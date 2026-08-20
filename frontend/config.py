import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuración del frontend.

    Lo único imprescindible es dónde vive el backend: esta aplicación no
    habla con la base, solo consume la API.
    """

    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
    SECRET_KEY = os.getenv("SECRET_KEY", "clave-de-desarrollo")

    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("FLASK_PORT", 3000))
