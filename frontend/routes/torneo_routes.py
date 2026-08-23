"""Pantallas de torneos."""
import auth
from flask import Blueprint, redirect, render_template, request, url_for

from services import api, torneos

torneo_bp = Blueprint("torneo", __name__, url_prefix="/torneos")


@torneo_bp.route("")
def listado():
    return render_template("torneos/listado.html", torneos=torneos.listar())


@torneo_bp.route("/historial")
def historial():
    return render_template("torneos/historial.html", tabla=torneos.tabla_historica())


@torneo_bp.route("/nuevo", methods=["GET", "POST"])
@auth.requiere_sesion
def nuevo():
    jugadores = api.get("/jugadores")

    if request.method == "GET":
        return render_template("torneos/nuevo.html", jugadores=jugadores, error=None)

    datos = {
        "nombre": request.form.get("nombre"),
        "modo": request.form.get("modo"),
        "fecha": request.form.get("fecha"),
        "lugar": request.form.get("lugar"),
        "descripcion": request.form.get("descripcion"),
        # Los ids llegan como texto del formulario y el backend los espera
        # como números.
        "jugadores_ids": [int(j) for j in request.form.getlist("jugadores_ids")],
    }
    if datos["modo"] == "rey_de_la_cancha":
        datos["vidas_iniciales"] = int(request.form.get("vidas_iniciales") or 0)

    try:
        creado = torneos.crear(datos)
    except api.ErrorDeApi as e:
        # Se vuelve al formulario con el motivo: el backend ya explica por
        # qué no se pudo, así que repetir esa validación acá sería tener la
        # misma regla escrita en dos lugares.
        return render_template("torneos/nuevo.html", jugadores=jugadores,
                               error=str(e), form=request.form), 400

    return redirect(url_for("torneo.detalle", torneo_id=creado["id"]))


@torneo_bp.route("/<int:torneo_id>")
def detalle(torneo_id):
    datos = torneos.detalle_completo(torneo_id)
    return render_template("torneos/detalle.html", **datos)


@torneo_bp.route("/<int:torneo_id>/jugar", methods=["GET", "POST"])
@auth.requiere_sesion
def jugar(torneo_id):
    """La pantalla que se usa durante el torneo: muestra el partido en
    curso y recibe el resultado."""
    if request.method == "POST":
        torneos.cargar_resultado(
            int(request.form["partido_id"]),
            {
                "ganador_id": int(request.form["ganador_id"]),
                "peleador1_id": _entero_o_nada(request.form.get("peleador1_id")),
                "peleador2_id": _entero_o_nada(request.form.get("peleador2_id")),
                "rondas_jugadas": _entero_o_nada(request.form.get("rondas_jugadas")),
            },
        )
        # Redirigir después de guardar evita que recargar la página vuelva
        # a enviar el mismo resultado.
        return redirect(url_for("torneo.jugar", torneo_id=torneo_id))

    partido = torneos.partido_actual(torneo_id)
    if partido is None:
        return redirect(url_for("torneo.detalle", torneo_id=torneo_id))

    nombres = {j["id"]: j["nombre"] for j in api.get("/jugadores")}
    return render_template(
        "torneos/jugar.html",
        torneo=torneos.obtener(torneo_id),
        partido=partido,
        nombre1=nombres.get(partido["jugador1_id"]),
        nombre2=nombres.get(partido["jugador2_id"]),
        peleadores=api.get("/peleadores"),
    )


def _entero_o_nada(valor):
    """Los campos opcionales llegan como texto vacío cuando no se
    completan, y el backend espera un número o nada."""
    return int(valor) if valor else None
