"""Pantallas de inicio y cierre de sesión."""
from flask import Blueprint, redirect, render_template, request, url_for

import auth
from services import api

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/entrar", methods=["GET", "POST"])
def login():
    siguiente = request.args.get("siguiente") or url_for("inicio.index")

    if request.method == "GET":
        return render_template("auth/login.html", error=None, siguiente=siguiente)

    try:
        respuesta = api.post("/auth/verificar", {
            "usuario": request.form.get("usuario"),
            "password": request.form.get("password"),
        })
    except api.ErrorDeApi as e:
        return render_template("auth/login.html", error=str(e), siguiente=siguiente), 401

    auth.iniciar_sesion(respuesta["usuario"])

    # Solo se vuelve a rutas de este sitio: si el destino llegara de
    # afuera, un enlace preparado podría mandar a alguien a otro dominio
    # justo después de entrar, que es una forma conocida de engaño.
    if not siguiente.startswith("/"):
        siguiente = url_for("inicio.index")
    return redirect(siguiente)


@auth_bp.route("/salir", methods=["POST"])
def logout():
    auth.cerrar_sesion()
    return redirect(url_for("inicio.index"))
