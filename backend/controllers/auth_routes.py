"""Endpoints de autenticación."""
from flask import Blueprint, jsonify, request

from services import usuario_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/verificar", methods=["POST"])
def verificar():
    """Comprueba credenciales y devuelve quién es.

    No emite ningún token: la sesión la maneja el frontend, que es quien
    tiene el navegador enfrente. El backend solo responde si estas
    credenciales son válidas o no."""
    datos = request.get_json(silent=True) or {}
    try:
        nombre = usuario_service.verificar(datos.get("usuario"), datos.get("password"))
        return jsonify({"usuario": nombre}), 200
    except usuario_service.CredencialesInvalidasError as e:
        return jsonify({"error": str(e)}), 401
