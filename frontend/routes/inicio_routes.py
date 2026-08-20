"""Pantalla de inicio."""
from flask import Blueprint, render_template

from services import api

inicio_bp = Blueprint("inicio", __name__)


@inicio_bp.route("/")
def index():
    # Si el backend no responde, la página se muestra igual con el motivo.
    # Una pantalla en blanco o un error 500 no le dirían a nadie qué pasó.
    try:
        jugadores = api.get("/jugadores")
        torneos = api.get("/torneos")
    except Exception as e:
        return render_template("inicio.html", error=str(e))

    return render_template(
        "inicio.html",
        cantidad_jugadores=len(jugadores),
        cantidad_torneos=len(torneos),
        error=None,
    )
