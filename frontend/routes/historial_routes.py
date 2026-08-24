"""Pantalla del historial de partidos."""
from flask import Blueprint, render_template, request

from services import api

historial_bp = Blueprint("historial", __name__, url_prefix="/historial")


@historial_bp.route("")
def index():
    filtros = {
        "jugador_id": request.args.get("jugador_id") or None,
        "torneo_id": request.args.get("torneo_id") or None,
        "peleador_id": request.args.get("peleador_id") or None,
    }
    resultado = api.get(
        "/historial",
        pagina=request.args.get("pagina", 1),
        **{k: v for k, v in filtros.items() if v},
    )

    return render_template(
        "historial/index.html",
        resultado=resultado,
        filtros=filtros,
        # Las listas para los desplegables de filtro.
        # Los filtros activos viajan en los enlaces de paginación: sin
        # eso, pasar de página perdería el filtro.
        filtros_activos={k: v for k, v in filtros.items() if v},
        jugadores=api.get("/jugadores"),
        torneos=api.get("/torneos"),
        peleadores=api.get("/peleadores"),
    )
