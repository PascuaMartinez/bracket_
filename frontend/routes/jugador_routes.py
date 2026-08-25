"""Pantallas de jugadores."""
import auth
from flask import Blueprint, redirect, render_template, request, url_for

from services import api, listado_jugadores, navegacion

jugador_bp = Blueprint("jugador", __name__, url_prefix="/jugadores")


@jugador_bp.route("")
def listado():
    # Los controles viajan en la dirección: así el listado ordenado se
    # puede compartir o guardar, y volver atrás no pierde el orden.
    orden = request.args.get("orden", listado_jugadores.ORDEN_POR_DEFECTO)
    descendente = request.args.get("dir") == "desc"
    ver_ocultos = request.args.get("ocultos") == "si"

    return render_template(
        "jugadores/listado.html",
        jugadores=listado_jugadores.obtener(orden, descendente, ver_ocultos),
        ordenes=listado_jugadores.ORDENES,
        orden=orden,
        descendente=descendente,
        ver_ocultos=ver_ocultos,
    )


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
    try:
        api.delete(f"/jugadores/{jugador_id}")
    except api.ErrorDeApi as e:
        # El backend rechaza sacar a alguien de un torneo en curso: ese
        # motivo tiene que llegar a quien lo intentó.
        return render_template("jugadores/detalle.html",
                               jugador=api.get(f"/jugadores/{jugador_id}"),
                               estadisticas=api.get(f"/jugadores/{jugador_id}/estadisticas"),
                               anterior=None, siguiente=None, error=str(e)), 400

    return redirect(url_for("jugador.listado"))


@jugador_bp.route("/<int:jugador_id>/mostrar", methods=["POST"])
@auth.requiere_sesion
def mostrar(jugador_id):
    api.post(f"/jugadores/{jugador_id}/mostrar", {})
    return redirect(url_for("jugador.listado", ocultos="si"))


@jugador_bp.route("/<int:jugador_id>")
def detalle(jugador_id):
    # El mismo listado que se usa para navegar: así las flechas siguen el
    # orden que se ve en pantalla y no otro.
    todos = api.get("/jugadores")
    anterior, siguiente = navegacion.vecinos(todos, jugador_id)

    return render_template(
        "jugadores/detalle.html",
        jugador=api.get(f"/jugadores/{jugador_id}"),
        estadisticas=api.get(f"/jugadores/{jugador_id}/estadisticas"),
        anterior=anterior,
        siguiente=siguiente,
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
