"""Endpoints de torneos."""
from flask import Blueprint, jsonify, request, send_file

from services import (
    estadisticas_torneo_service, exportar_service, grupos_consulta_service,
    tabla_historica_service, tabla_service, torneo_service,
)

torneo_bp = Blueprint("torneo", __name__, url_prefix="/torneos")


@torneo_bp.route("", methods=["GET"])
def listar():
    return jsonify(torneo_service.listar_torneos()), 200


@torneo_bp.route("/tabla-historica", methods=["GET"])
def tabla_historica():
    return jsonify(tabla_historica_service.calcular_tabla_historica()), 200


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


@torneo_bp.route("/<int:torneo_id>/grupos", methods=["GET"])
def grupos(torneo_id):
    try:
        torneo_service.obtener_torneo(torneo_id)
        return jsonify(grupos_consulta_service.obtener_grupos(torneo_id)), 200
    except torneo_service.TorneoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@torneo_bp.route("/<int:torneo_id>/grupos/<int:grupo_id>/resolver", methods=["POST"])
def resolver_empate(torneo_id, grupo_id):
    """Decide a mano si un jugador clasifica, cuando quedó un empate."""
    from services import partido_service

    datos = request.get_json(silent=True) or {}
    partido_service.resolver_empate(
        torneo_id, grupo_id,
        datos.get("jugador_id"),
        bool(datos.get("clasifica")),
        datos.get("observacion"),
    )
    return "", 204


@torneo_bp.route("/<int:torneo_id>/repetir-desempate", methods=["POST"])
def repetir_desempate(torneo_id):
    """Vuelve a jugar un desempate que no resolvió."""
    from services import partido_service

    datos = request.get_json(silent=True) or {}
    cantidad = partido_service.repetir_desempate(
        torneo_id, datos.get("jugadores_ids", [])
    )
    return jsonify({"partidos": cantidad}), 200


@torneo_bp.route("/<int:torneo_id>/imagen", methods=["GET"])
def imagen(torneo_id):
    """La tabla del torneo como PNG, para compartir."""
    try:
        torneo = torneo_service.obtener_torneo(torneo_id)
    except torneo_service.TorneoNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404

    imagen_generada = exportar_service.generar(torneo_id)
    # El nombre del archivo sale del torneo: descargar veinte imágenes
    # llamadas "imagen.png" no le sirve a nadie.
    nombre = "".join(c if c.isalnum() or c in " -_" else "" for c in torneo["nombre"])
    return send_file(
        imagen_generada, mimetype="image/png",
        download_name=f"{nombre or 'torneo'}.png",
    )


@torneo_bp.route("/<int:torneo_id>/estadisticas", methods=["GET"])
def estadisticas(torneo_id):
    try:
        return jsonify(
            estadisticas_torneo_service.obtener_estadisticas(torneo_id)
        ), 200
    except estadisticas_torneo_service.TorneoNoEncontradoError as e:
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
            vidas_iniciales=datos.get("vidas_iniciales"),
            cantidad_grupos=datos.get("cantidad_grupos"),
            cupos_eliminacion=datos.get("cupos_eliminacion"),
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
