from flask import Flask, request

from config import Config
from services import cache
from controllers.jugador_routes import jugador_bp
from controllers.peleador_routes import peleador_bp
from controllers.torneo_routes import torneo_bp
from controllers.auth_routes import auth_bp
from controllers.partido_routes import partido_bp


def create_app():
    """
    Se arma la app dentro de una función y no a nivel de módulo para poder
    crear instancias independientes en las pruebas, cada una con su
    configuración, sin arrastrar estado entre una y otra.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(jugador_bp)
    app.register_blueprint(peleador_bp)
    app.register_blueprint(torneo_bp)
    app.register_blueprint(partido_bp)
    app.register_blueprint(auth_bp)

    @app.after_request
    def invalidar_cache_si_hubo_cambios(respuesta):
        """
        Vacía el cache después de cualquier escritura exitosa.

        Va acá y no en cada servicio que modifica datos a propósito: son
        muchos, y alcanzaría con olvidarse en uno para que la aplicación
        muestre datos viejos sin ninguna señal de que algo anda mal. Del
        lado del método HTTP, en cambio, la regla es simple y no hay forma
        de saltearla: si el pedido modificó algo y salió bien, el cache ya
        no sirve.
        """
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if 200 <= respuesta.status_code < 400:
                cache.invalidar_todo()
        return respuesta

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=Config.PORT, debug=Config.DEBUG)
