"""
Endpoints de jugadores.

La capa de arriba: traduce HTTP a llamadas al servicio y de vuelta. Acá
no hay reglas del negocio ni SQL -- si un controlador empieza a decidir
cosas, esa decisión pertenece al servicio.

Su otro trabajo es traducir las excepciones del dominio al código HTTP
que corresponde, para que el servicio pueda ignorar que HTTP existe.
"""
from flask import Blueprint, jsonify, request

from services import estadisticas_service, imagenes_service, jugador_service
from repositories import jugador_repository

jugador_bp = Blueprint("jugador", __name__, url_prefix="/jugadores")


@jugador_bp.route("", methods=["GET"])
def listar():
    # Los ocultos se piden explícitamente con ?incluir_ocultos=si
    incluir = request.args.get("incluir_ocultos") == "si"
    return jsonify(jugador_service.listar_jugadores(incluir)), 200


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


@jugador_bp.route("/<int:jugador_id>/imagen", methods=["POST"])
def subir_imagen(jugador_id):
    """Recibe la imagen como archivo, no como JSON.

    Un archivo en JSON iría codificado en base64, lo que lo agranda un
    tercio y obliga a cargarlo entero en memoria de los dos lados."""
    try:
        jugador_service.obtener_jugador(jugador_id)
    except jugador_service.JugadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404

    tipo = request.form.get("tipo", "vertical")
    campo = "imagen_icono_path" if tipo == "icono" else "imagen_vertical_path"

    try:
        ruta = imagenes_service.guardar(request.files.get("imagen"), "jugadores")
    except imagenes_service.ImagenInvalidaError as e:
        return jsonify({"error": str(e)}), 400

    if ruta is None:
        return jsonify({"error": "No se recibió ninguna imagen"}), 400

    jugador_repository.actualizar_imagen(jugador_id, campo, ruta)
    return jsonify(jugador_service.obtener_jugador(jugador_id)), 200


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
        # Se devuelve qué se hizo -- borrado u ocultado -- porque son
        # cosas distintas y quien lo pidió tiene derecho a saber cuál pasó.
        resultado = jugador_service.eliminar_jugador(jugador_id)
        return jsonify({"resultado": resultado}), 200
    except jugador_service.JugadorInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except jugador_service.JugadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@jugador_bp.route("/<int:jugador_id>/mostrar", methods=["POST"])
def mostrar(jugador_id):
    try:
        jugador_service.mostrar_jugador(jugador_id)
        return jsonify(jugador_service.obtener_jugador(jugador_id)), 200
    except jugador_service.JugadorNoEncontradoError as e:
        return jsonify({"error": str(e)}), 404


@jugador_bp.route("/<int:jugador_id>/pronostico/<int:rival_id>", methods=["GET"])
def pronostico(jugador_id, rival_id):
    """Qué tan probable es que uno le gane al otro, según sus ratings."""
    from services import rating_service, tabla_historica_service

    tabla = tabla_historica_service.calcular_tabla_historica()
    ratings = {f["jugador_id"]: f.get("rating") for f in tabla}

    if jugador_id not in ratings or rival_id not in ratings:
        return jsonify({"error": "Alguno de los dos no jugó ningún torneo"}), 404

    return jsonify({
        "jugador": {"id": jugador_id, "rating": ratings[jugador_id]},
        "rival": {"id": rival_id, "rating": ratings[rival_id]},
        "probabilidad": round(
            rating_service.probabilidad(ratings[jugador_id], ratings[rival_id]), 3
        ),
    }), 200
