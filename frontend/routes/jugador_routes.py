"""Pantallas de jugadores."""
import auth
from flask import Blueprint, redirect, render_template, request, url_for

from services import api

jugador_bp = Blueprint("jugador", __name__, url_prefix="/jugadores")


@jugador_bp.route("")
def listado():
    return render_template("jugadores/listado.html", jugadores=api.get("/jugadores"))


@jugador_bp.route("/nuevo", methods=["GET", "POST"])
@auth.requiere_sesion
def nuevo():
    if request.method == "GET":
        return render_template("jugadores/formulario.html", jugador=None, error=None)

    try:
        creado = api.post("/jugadores", _datos_del_formulario())
        _subir_imagenes(creado["id"])
    except api.ErrorDeApi as e:
        # Se vuelve al formulario con el motivo, conservando lo que la
        # persona ya había escrito: perder el formulario entero por un
        # campo mal cargado es innecesariamente molesto.
        return render_template("jugadores/formulario.html", jugador=request.form,
                               error=str(e)), 400

    return redirect(url_for("jugador.listado"))


@jugador_bp.route("/<int:jugador_id>/editar", methods=["GET", "POST"])
@auth.requiere_sesion
def editar(jugador_id):
    if request.method == "GET":
        return render_template("jugadores/formulario.html",
                               jugador=api.get(f"/jugadores/{jugador_id}"), error=None)

    try:
        api.put(f"/jugadores/{jugador_id}", _datos_del_formulario())
        _subir_imagenes(jugador_id)
    except api.ErrorDeApi as e:
        return render_template("jugadores/formulario.html", jugador=request.form,
                               error=str(e)), 400

    return redirect(url_for("jugador.detalle", jugador_id=jugador_id))


@jugador_bp.route("/<int:jugador_id>/eliminar", methods=["POST"])
@auth.requiere_sesion
def eliminar(jugador_id):
    """Solo por POST y nunca por GET: un enlace que borra puede
    dispararse solo si algo precarga la página."""
    api.delete(f"/jugadores/{jugador_id}")
    return redirect(url_for("jugador.listado"))


@jugador_bp.route("/<int:jugador_id>")
def detalle(jugador_id):
    return render_template(
        "jugadores/detalle.html",
        jugador=api.get(f"/jugadores/{jugador_id}"),
        estadisticas=api.get(f"/jugadores/{jugador_id}/estadisticas"),
    )


def _datos_del_formulario():
    return {
        "nombre": request.form.get("nombre"),
        # Un campo de fecha vacío llega como texto vacío, y el backend
        # espera una fecha o nada.
        "fecha_nacimiento": request.form.get("fecha_nacimiento") or None,
    }


def _subir_imagenes(jugador_id):
    """Sube las imágenes que se hayan elegido.

    Van en pedidos aparte del alta y no en el mismo: el jugador tiene que
    existir antes de poder colgarle una imagen. La contra es que si falla
    la imagen el jugador ya quedó creado, que es preferible al revés --
    perder los datos cargados por una foto que no subió.
    """
    for campo, tipo in (("imagen_vertical", "vertical"), ("imagen_icono", "icono")):
        archivo = request.files.get(campo)
        if archivo and archivo.filename:
            api.subir_archivo(f"/jugadores/{jugador_id}/imagen", archivo, {"tipo": tipo})
