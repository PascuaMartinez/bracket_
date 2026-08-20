from flask import Flask

from config import Config
from routes.inicio_routes import inicio_bp
from routes.jugador_routes import jugador_bp
from routes.peleador_routes import peleador_bp
from routes.torneo_routes import torneo_bp


# Los formatos se guardan con su nombre técnico. Traducirlos a algo
# legible se hace en un único lugar: si se agrega un formato y se olvida
# sumarlo acá, se muestra el nombre técnico con espacios en vez de romper.
NOMBRES_DE_FORMATO = {
    "todos_contra_todos": "Todos contra todos",
    "eliminacion": "Eliminación directa",
    "rey_de_la_cancha": "Rey de la cancha",
}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.template_filter("nombre_formato")
    def nombre_formato(valor):
        return NOMBRES_DE_FORMATO.get(valor, (valor or "").replace("_", " "))

    @app.template_filter("nombres_y_veces")
    def nombres_y_veces(lista, campo):
        """Muestra una lista de rivales con su número al lado.

        Las estadísticas devuelven TODOS los que empatan en el máximo, no
        uno solo, así que la plantilla tiene que poder mostrar varios."""
        if not lista:
            return "—"
        return ", ".join(f"{r['nombre']} ({r[campo]})" for r in lista)

    @app.template_filter("nombre_jugador")
    def nombre_jugador(jugador_id):
        """Los partidos vienen con ids, no con nombres. Se resuelve acá y
        no en cada ruta para no repetir el mismo mapeo en todas."""
        if jugador_id is None:
            return "—"
        from services import api
        for j in api.get("/jugadores"):
            if j["id"] == jugador_id:
                return j["nombre"]
        return "?"

    app.register_blueprint(inicio_bp)
    app.register_blueprint(jugador_bp)
    app.register_blueprint(peleador_bp)
    app.register_blueprint(torneo_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=Config.PORT, debug=Config.DEBUG)
