"""Pantalla de configuración."""
import auth
from flask import Blueprint, redirect, render_template, request, url_for

from services import api, configuracion

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


@configuracion_bp.route("", methods=["GET", "POST"])
@auth.requiere_sesion
def index():
    if request.method == "POST":
        try:
            configuracion.actualizar({
                "nombre_club": request.form.get("nombre_club"),
                "texto_inicio": request.form.get("texto_inicio"),
                "texto_formatos": request.form.get("texto_formatos"),
            })
        except api.ErrorDeApi as e:
            return render_template(
                "configuracion/index.html", config=request.form,
                estadisticas=configuracion.listar_estadisticas(), error=str(e),
            ), 400
        return redirect(url_for("configuracion.index"))

    return render_template(
        "configuracion/index.html",
        config=configuracion.obtener(),
        estadisticas=configuracion.listar_estadisticas(),
        error=None,
    )


@configuracion_bp.route("/estadisticas", methods=["POST"])
@auth.requiere_sesion
def guardar_estadisticas():
    """El formulario manda las VISIBLES (las tildadas); lo que se guarda
    son las ocultas. Se invierte acá porque para quien configura es más
    natural marcar lo que quiere ver que lo que quiere esconder."""
    todas = {e["clave"] for e in configuracion.listar_estadisticas()}
    visibles = set(request.form.getlist("visibles"))
    configuracion.guardar_estadisticas_ocultas(sorted(todas - visibles))
    return redirect(url_for("configuracion.index"))
