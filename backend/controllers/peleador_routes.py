"""Endpoints de personajes."""
from flask import Blueprint, jsonify, request

from services import peleador_service

peleador_bp = Blueprint("peleador", __name__, url_prefix="/peleadores")


@peleador_bp.route("", methods=["GET"])
def listar():
    return jsonify(peleador_service.listar_peleadores()), 200


@peleador_bp.route("/<int:peleador_id>", methods=["GET"])
def obtener(peleador_id):
    try:
        return jsonify(peleador_service.obtener_peleador(peleador_id)), 200
    except peleador_service.PeleadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@peleador_bp.route("", methods=["POST"])
def crear():
    datos = request.get_json(silent=True) or {}
    try:
        return jsonify(peleador_service.crear_peleador(datos.get("nombre"))), 201
    except peleador_service.PeleadorInvalidoError as e:
        return jsonify({"error": str(e)}), 400


@peleador_bp.route("/<int:peleador_id>", methods=["PUT"])
def actualizar(peleador_id):
    datos = request.get_json(silent=True) or {}
    try:
        return jsonify(peleador_service.actualizar_peleador(peleador_id, datos.get("nombre"))), 200
    except peleador_service.PeleadorInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except peleador_service.PeleadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@peleador_bp.route("/<int:peleador_id>", methods=["DELETE"])
def eliminar(peleador_id):
    try:
        peleador_service.eliminar_peleador(peleador_id)
        return "", 204
    except peleador_service.PeleadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404
