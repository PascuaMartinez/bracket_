"""Endpoint del historial de partidos."""
from flask import Blueprint, jsonify, request

from services import historial_service

historial_bp = Blueprint("historial", __name__, url_prefix="/historial")


@historial_bp.route("", methods=["GET"])
def buscar():
    return jsonify(historial_service.buscar(
        jugador_id=_entero(request.args.get("jugador_id")),
        torneo_id=_entero(request.args.get("torneo_id")),
        peleador_id=_entero(request.args.get("peleador_id")),
        pagina=_entero(request.args.get("pagina")) or 1,
    )), 200


def _entero(valor):
    """Los filtros llegan como texto y pueden venir vacíos o con
    cualquier cosa. Un valor que no es número se ignora en vez de romper:
    es un filtro, no un dato crítico."""
    try:
        return int(valor) if valor else None
    except (TypeError, ValueError):
        return None
