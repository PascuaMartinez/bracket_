"""
Endpoints de jugadores.

La capa de arriba: traduce HTTP a llamadas al servicio y de vuelta. Acá
no hay reglas del negocio ni SQL -- si un controlador empieza a decidir
cosas, esa decisión pertenece al servicio.

Su otro trabajo es traducir las excepciones del dominio al código HTTP
que corresponde, para que el servicio pueda ignorar que HTTP existe.
"""
from flask import Blueprint, jsonify, request

from services import estadisticas_service, jugador_service

jugador_bp = Blueprint("jugador", __name__, url_prefix="/jugadores")


@jugador_bp.route("", methods=["GET"])
def listar():
    return jsonify(jugador_service.listar_jugadores()), 200


@jugador_bp.route("/<int:jugador_id>", methods=["GET"])
def obtener(jugador_id):
    try:
        return jsonify(jugador_service.obtener_jugador(jugador_id)), 200
    except jugador_service.JugadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@jugador_bp.route("/<int:jugador_id>/estadisticas", methods=["GET"])
def estadisticas(jugador_id):
    try:
        return jsonify(estadisticas_service.obtener_estadisticas(jugador_id)), 200
    except estadisticas_service.JugadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@jugador_bp.route("", methods=["POST"])
def crear():
    datos = request.get_json(silent=True) or {}
    try:
        nuevo = jugador_service.crear_jugador(
            datos.get("nombre"), datos.get("fecha_nacimiento")
        )
        # 201 y no 200: se creó un recurso nuevo.
        return jsonify(nuevo), 201
    except jugador_service.JugadorInvalidoError as e:
        return jsonify({"error": str(e)}), 400


@jugador_bp.route("/<int:jugador_id>", methods=["PUT"])
def actualizar(jugador_id):
    datos = request.get_json(silent=True) or {}
    try:
        actualizado = jugador_service.actualizar_jugador(
            jugador_id, datos.get("nombre"), datos.get("fecha_nacimiento")
        )
        return jsonify(actualizado), 200
    except jugador_service.JugadorInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except jugador_service.JugadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@jugador_bp.route("/<int:jugador_id>", methods=["DELETE"])
def eliminar(jugador_id):
    try:
        jugador_service.eliminar_jugador(jugador_id)
        # 204: salió bien y no hay nada que devolver.
        return "", 204
    except jugador_service.JugadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404
