"""Pantallas de jugadores."""
from flask import Blueprint, render_template

from services import api

jugador_bp = Blueprint("jugador", __name__, url_prefix="/jugadores")


@jugador_bp.route("")
def listado():
    return render_template("jugadores/listado.html", jugadores=api.get("/jugadores"))
