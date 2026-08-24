"""Endpoints de personajes."""
from flask import Blueprint, jsonify, request

from repositories import peleador_repository
from services import (
    estadisticas_peleador_service, imagenes_service, peleador_service,
)

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


@peleador_bp.route("/<int:peleador_id>/estadisticas", methods=["GET"])
def estadisticas(peleador_id):
    try:
        return jsonify(
            estadisticas_peleador_service.obtener_estadisticas(peleador_id)
        ), 200
    except estadisticas_peleador_service.PeleadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@peleador_bp.route("/<int:peleador_id>/imagen", methods=["POST"])
def subir_imagen(peleador_id):
    try:
        peleador_service.obtener_peleador(peleador_id)
    except peleador_service.PeleadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404

    try:
        ruta = imagenes_service.guardar(request.files.get("imagen"), "peleadores")
    except imagenes_service.ImagenInvalidaError as e:
        return jsonify({"error": str(e)}), 400

    if ruta is None:
        return jsonify({"error": "No se recibió ninguna imagen"}), 400

    peleador_repository.actualizar_imagen(peleador_id, ruta)
    return jsonify(peleador_service.obtener_peleador(peleador_id)), 200


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
