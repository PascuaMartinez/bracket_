"""Pantallas de personajes."""
from flask import Blueprint, redirect, render_template, request, url_for

from services import api

peleador_bp = Blueprint("peleador", __name__, url_prefix="/peleadores")


@peleador_bp.route("")
def listado():
    return render_template("peleadores/listado.html", peleadores=api.get("/peleadores"))


@peleador_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "GET":
        return render_template("peleadores/formulario.html", peleador=None, error=None)

    try:
        api.post("/peleadores", {"nombre": request.form.get("nombre")})
    except api.ErrorDeApi as e:
        # El backend rechaza los nombres repetidos: mostrar ese motivo tal
        # como viene evita tener la misma regla escrita en los dos lados.
        return render_template("peleadores/formulario.html", peleador=request.form,
                               error=str(e)), 400

    return redirect(url_for("peleador.listado"))


@peleador_bp.route("/<int:peleador_id>/editar", methods=["GET", "POST"])
def editar(peleador_id):
    if request.method == "GET":
        return render_template("peleadores/formulario.html",
                               peleador=api.get(f"/peleadores/{peleador_id}"), error=None)

    try:
        api.put(f"/peleadores/{peleador_id}", {"nombre": request.form.get("nombre")})
    except api.ErrorDeApi as e:
        return render_template("peleadores/formulario.html", peleador=request.form,
                               error=str(e)), 400

    return redirect(url_for("peleador.listado"))


@peleador_bp.route("/<int:peleador_id>/eliminar", methods=["POST"])
def eliminar(peleador_id):
    api.delete(f"/peleadores/{peleador_id}")
    return redirect(url_for("peleador.listado"))
