"""
Sesión de la aplicación.

La sesión vive en una cookie firmada por Flask: el navegador la guarda
pero no puede modificarla sin invalidar la firma, así que nadie puede
declararse administrador editándola.
"""
from functools import wraps

from flask import redirect, request, session, url_for


def usuario_actual():
    return session.get("usuario")


def hay_sesion():
    return usuario_actual() is not None


def iniciar_sesion(nombre_usuario):
    session["usuario"] = nombre_usuario


def cerrar_sesion():
    session.pop("usuario", None)


def requiere_sesion(vista):
    """
    Protege las rutas que modifican datos.

    Ver es público -- el grupo mira los resultados sin cuenta -- pero
    crear, editar y borrar necesitan sesión.

    Al redirigir se guarda a dónde se quería ir, para volver ahí después
    de entrar en vez de dejar a la persona en el inicio buscando de nuevo
    lo que estaba por hacer.
    """
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if not hay_sesion():
            return redirect(url_for("auth.login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltorio
