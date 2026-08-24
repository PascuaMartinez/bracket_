"""Endpoints de configuración."""
from flask import Blueprint, jsonify, request

from services import configuracion_service

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


@configuracion_bp.route("", methods=["GET"])
def obtener():
    return jsonify(configuracion_service.obtener()), 200


@configuracion_bp.route("", methods=["PUT"])
def actualizar():
    datos = request.get_json(silent=True) or {}
    try:
        return jsonify(configuracion_service.actualizar(
            datos.get("nombre_club"),
            datos.get("texto_inicio"),
            datos.get("texto_formatos"),
        )), 200
    except configuracion_service.ConfiguracionInvalidaError as e:
        return jsonify({"error": str(e)}), 400


@configuracion_bp.route("/estadisticas", methods=["GET"])
def listar_estadisticas():
    return jsonify(configuracion_service.listar_estadisticas()), 200


@configuracion_bp.route("/estadisticas", methods=["PUT"])
def guardar_estadisticas():
    datos = request.get_json(silent=True) or {}
    try:
        ocultas = configuracion_service.guardar_estadisticas_ocultas(
            datos.get("ocultas", [])
        )
        return jsonify({"ocultas": ocultas}), 200
    except configuracion_service.ConfiguracionInvalidaError as e:
        return jsonify({"error": str(e)}), 400
