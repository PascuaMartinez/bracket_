from flask import Flask

from config import Config
from routes.inicio_routes import inicio_bp
from routes.jugador_routes import jugador_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(inicio_bp)
    app.register_blueprint(jugador_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=Config.PORT, debug=Config.DEBUG)
