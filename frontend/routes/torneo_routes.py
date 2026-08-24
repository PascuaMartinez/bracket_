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
    # Cada formato pide datos propios. Se mandan solo los que
    # corresponden: el backend ignora el resto, pero enviarlos igual
    # haría más difícil entender qué necesita cada uno.
    if datos["modo"] == "rey_de_la_cancha":
        datos["vidas_iniciales"] = int(request.form.get("vidas_iniciales") or 0)
    elif datos["modo"] == "grupos_eliminacion":
        datos["cantidad_grupos"] = int(request.form.get("cantidad_grupos") or 0)
        datos["cupos_eliminacion"] = int(request.form.get("cupos_eliminacion") or 0)

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
    # Los grupos solo existen en un formato: se piden aparte y solo
    # cuando corresponde, en vez de que todos los torneos paguen una
    # llamada que casi siempre viene vacía.
    if datos["torneo"]["modo"] == "grupos_eliminacion":
        datos["grupos"] = torneos.grupos(torneo_id)
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

    # Los pospuestos se muestran junto al partido actual: si quedaron
    # afuera de la vista, es fácil terminar el torneo sin acordarse de
    # que faltaban jugar.
    lista_pospuestos = torneos.pospuestos(torneo_id)

    nombres = {j["id"]: j["nombre"] for j in api.get("/jugadores")}
    return render_template(
        "torneos/jugar.html",
        torneo=torneos.obtener(torneo_id),
        partido=partido,
        nombre1=nombres.get(partido["jugador1_id"]),
        nombre2=nombres.get(partido["jugador2_id"]),
        peleadores=api.get("/peleadores"),
        pospuestos=lista_pospuestos,
        nombres=nombres,
    )


def _entero_o_nada(valor):
    """Los campos opcionales llegan como texto vacío cuando no se
    completan, y el backend espera un número o nada."""
    return int(valor) if valor else None


@torneo_bp.route("/<int:torneo_id>/editar", methods=["GET", "POST"])
@auth.requiere_sesion
def editar(torneo_id):
    """
    Solo se editan los datos descriptivos: nombre, fecha, lugar y
    descripción.

    El formato y los participantes NO se pueden cambiar. Con partidos ya
    jugados, cambiar el formato dejaría el torneo inconsistente con lo que
    efectivamente pasó, y sacar a alguien que ya jugó dejaría resultados
    huérfanos. Si hay que corregir eso, corresponde borrar el torneo y
    rehacerlo.
    """
    if request.method == "GET":
        return render_template("torneos/editar.html",
                               torneo=torneos.obtener(torneo_id), error=None)

    try:
        torneos.actualizar(torneo_id, {
            "nombre": request.form.get("nombre"),
            "fecha": request.form.get("fecha"),
            "lugar": request.form.get("lugar"),
            "descripcion": request.form.get("descripcion"),
        })
    except api.ErrorDeApi as e:
        return render_template("torneos/editar.html", torneo=request.form,
                               error=str(e)), 400

    return redirect(url_for("torneo.detalle", torneo_id=torneo_id))


@torneo_bp.route("/<int:torneo_id>/eliminar", methods=["POST"])
@auth.requiere_sesion
def eliminar(torneo_id):
    torneos.eliminar(torneo_id)
    return redirect(url_for("torneo.listado"))


@torneo_bp.route("/<int:torneo_id>/partidos/<int:partido_id>/posponer", methods=["POST"])
@auth.requiere_sesion
def posponer(torneo_id, partido_id):
    torneos.posponer(partido_id)
    return redirect(url_for("torneo.jugar", torneo_id=torneo_id))


@torneo_bp.route("/<int:torneo_id>/partidos/<int:partido_id>/retomar", methods=["POST"])
@auth.requiere_sesion
def retomar(torneo_id, partido_id):
    torneos.retomar(partido_id)
    return redirect(url_for("torneo.jugar", torneo_id=torneo_id))


@torneo_bp.route("/<int:torneo_id>/grupos/<int:grupo_id>/resolver", methods=["POST"])
@auth.requiere_sesion
def resolver_empate(torneo_id, grupo_id):
    torneos.resolver_empate(
        torneo_id, grupo_id,
        int(request.form["jugador_id"]),
        request.form.get("clasifica") == "si",
        request.form.get("observacion") or None,
    )
    return redirect(url_for("torneo.detalle", torneo_id=torneo_id))
