from flask import Flask

from config import Config
from controllers.jugador_routes import jugador_bp


def create_app():
    """
    Se arma la app dentro de una función y no a nivel de módulo para poder
    crear instancias independientes en las pruebas, cada una con su
    configuración, sin arrastrar estado entre una y otra.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(jugador_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=Config.PORT, debug=Config.DEBUG)
