"""Endpoints de partidos."""
from flask import Blueprint, jsonify, request

from services import partido_service

partido_bp = Blueprint("partido", __name__)


@partido_bp.route("/torneos/<int:torneo_id>/partidos", methods=["GET"])
def listar(torneo_id):
    return jsonify(partido_service.listar_partidos(torneo_id)), 200


@partido_bp.route("/torneos/<int:torneo_id>/partido-actual", methods=["GET"])
def actual(torneo_id):
    """
    El próximo partido con todo el contexto que necesita la pantalla:
    en qué instancia se juega, cómo vienen entre ellos, y las vidas si el
    formato las usa.

    Va todo junto y no en llamadas separadas porque es una sola pantalla:
    pedirlo en tres pedidos la haría más lenta sin ganar nada.
    """
    from repositories import torneo_repository
    from services import vidas_service

    partido = partido_service.obtener_partido_actual(torneo_id)
    if partido is None:
        # 204: la consulta salió bien, simplemente no hay partido
        # pendiente. Un 404 diría que la dirección no existe.
        return "", 204

    torneo = torneo_repository.obtener_por_id(torneo_id)

    return jsonify({
        **partido,
        "fase": partido_service.describir_fase(torneo, partido),
        "historial": partido_service.historial_entre(
            partido["jugador1_id"], partido["jugador2_id"]
        ),
        "vidas": vidas_service.vidas_de(torneo, [partido["jugador1_id"],
                                                 partido["jugador2_id"]]),
    }), 200


@partido_bp.route("/partidos/<int:partido_id>/resultado", methods=["POST"])
def cargar_resultado(partido_id):
    datos = request.get_json(silent=True) or {}
    try:
        partido = partido_service.cargar_resultado(
            partido_id,
            datos.get("ganador_id"),
            datos.get("peleador1_id"),
            datos.get("peleador2_id"),
            datos.get("rondas_jugadas"),
        )
        return jsonify(partido), 200
    except partido_service.ResultadoInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except partido_service.PartidoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@partido_bp.route("/torneos/<int:torneo_id>/pospuestos", methods=["GET"])
def pospuestos(torneo_id):
    return jsonify(partido_service.listar_pospuestos(torneo_id)), 200


@partido_bp.route("/partidos/<int:partido_id>/posponer", methods=["POST"])
def posponer(partido_id):
    try:
        partido_service.posponer(partido_id)
        return "", 204
    except partido_service.ResultadoInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except partido_service.PartidoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@partido_bp.route("/partidos/<int:partido_id>/retomar", methods=["POST"])
def retomar(partido_id):
    try:
        partido_service.retomar(partido_id)
        return "", 204
    except partido_service.ResultadoInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except partido_service.PartidoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404
