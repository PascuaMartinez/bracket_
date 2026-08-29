from flask import Flask

import auth
from config import Config
from routes.auth_routes import auth_bp
from routes.configuracion_routes import configuracion_bp
from routes.historial_routes import historial_bp
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

    # Disponible en todas las plantillas: los botones de crear y editar
    # solo se muestran con sesión iniciada. No es la protección -- esa
    # está en las rutas -- sino no ofrecer acciones que van a rebotar.
    def nombre_del_club():
        """El nombre configurado, o el del sistema si el backend no
        responde. Que el encabezado rompa la página entera por no poder
        leer un nombre sería desproporcionado."""
        try:
            from services import configuracion
            return configuracion.obtener().get("nombre_club") or "Bracket"
        except Exception:
            return "Bracket"

    app.jinja_env.globals["nombre_del_club"] = nombre_del_club
    app.jinja_env.globals["hay_sesion"] = auth.hay_sesion
    app.jinja_env.globals["usuario_actual"] = auth.usuario_actual

    # La imagen la genera el backend: el enlace apunta directo ahí en
    # vez de pasar por esta aplicación, que solo agregaría un salto.
    app.jinja_env.globals["url_imagen_torneo"] = (
        lambda torneo_id: f"{Config.API_BASE_URL}/torneos/{torneo_id}/imagen"
    )

    @app.template_filter("url_imagen")
    def url_imagen(ruta):
        """Las imágenes las sirve el backend, no esta aplicación: la ruta
        guardada es relativa y hay que anteponerle dónde vive."""
        if not ruta:
            return None
        return f"{Config.API_BASE_URL}/static/{ruta}"

    @app.template_filter("emoji_puesto")
    def emoji_puesto(fila, modo=None):
        """
        El reconocimiento que le corresponde a un puesto.

        El podio es igual en todos los formatos. Debajo de eso el criterio
        cambia porque el quinto puesto significa cosas distintas: en una
        tabla es el quinto de la lista, y en un cuadro es alguien que cayó
        en cuartos, o sea que estuvo entre los ocho mejores.

        Por eso el 5 y el 8 nunca conviven: cada uno es el último escalón
        reconocido en su tipo de formato. Debajo de ahí no hay
        reconocimiento en ninguno de los dos.
        """
        puesto = fila.get("puesto") if isinstance(fila, dict) else fila
        if not puesto:
            return ""

        if puesto == 1:
            return "🥇"
        if puesto == 2:
            return "🥈"
        if puesto == 3:
            return "🥉"
        if puesto == 4:
            return "4️⃣"

        # En los formatos con cuadro, quedar quinto es haber caído en
        # cuartos: se reconoce por estar entre los ocho mejores.
        con_cuadro = modo in ("eliminacion", "grupos_eliminacion")
        if puesto == 5:
            return "8️⃣" if con_cuadro else "5️⃣"

        return ""

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

    @app.template_filter("nombres_con_record")
    def nombres_con_record(lista):
        """Muestra rivales con su récord: 'Ky (2-5)'. El récord importa
        porque sin él, saber que alguien es 'el peor enemigo' no dice qué
        tan mal le fue."""
        if not lista:
            return "—"
        return ", ".join(
            f"{r['nombre']} ({r['ganados']}-{r['perdidos']})" for r in lista
        )

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(historial_bp)
    app.register_blueprint(inicio_bp)
    app.register_blueprint(jugador_bp)
    app.register_blueprint(peleador_bp)
    app.register_blueprint(torneo_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=Config.PORT, debug=Config.DEBUG)
