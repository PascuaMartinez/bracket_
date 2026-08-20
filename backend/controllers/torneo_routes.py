"""Endpoints de torneos."""
from flask import Blueprint, jsonify, request

from services import tabla_service, torneo_service

torneo_bp = Blueprint("torneo", __name__, url_prefix="/torneos")


@torneo_bp.route("", methods=["GET"])
def listar():
    return jsonify(torneo_service.listar_torneos()), 200


@torneo_bp.route("/<int:torneo_id>", methods=["GET"])
def obtener(torneo_id):
    try:
        return jsonify(torneo_service.obtener_torneo(torneo_id)), 200
    except torneo_service.TorneoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@torneo_bp.route("/<int:torneo_id>/jugadores", methods=["GET"])
def participantes(torneo_id):
    try:
        return jsonify(torneo_service.obtener_participantes(torneo_id)), 200
    except torneo_service.TorneoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@torneo_bp.route("/<int:torneo_id>/tabla", methods=["GET"])
def tabla(torneo_id):
    try:
        torneo_service.obtener_torneo(torneo_id)  # 404 si no existe
        return jsonify(tabla_service.calcular_tabla(torneo_id)), 200
    except torneo_service.TorneoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@torneo_bp.route("", methods=["POST"])
def crear():
    datos = request.get_json(silent=True) or {}
    try:
        nuevo = torneo_service.crear_torneo(
            nombre=datos.get("nombre"),
            modo=datos.get("modo"),
            fecha=datos.get("fecha"),
            jugadores_ids=datos.get("jugadores_ids"),
            descripcion=datos.get("descripcion"),
            lugar=datos.get("lugar"),
        )
        return jsonify(nuevo), 201
    except torneo_service.TorneoInvalidoError as e:
        return jsonify({"error": str(e)}), 400


@torneo_bp.route("/<int:torneo_id>", methods=["PUT"])
def actualizar(torneo_id):
    datos = request.get_json(silent=True) or {}
    try:
        actualizado = torneo_service.actualizar_torneo(
            torneo_id, datos.get("nombre"), datos.get("fecha"),
            datos.get("descripcion"), datos.get("lugar"),
        )
        return jsonify(actualizado), 200
    except torneo_service.TorneoInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except torneo_service.TorneoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@torneo_bp.route("/<int:torneo_id>", methods=["DELETE"])
def eliminar(torneo_id):
    try:
        torneo_service.eliminar_torneo(torneo_id)
        return "", 204
    except torneo_service.TorneoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404
