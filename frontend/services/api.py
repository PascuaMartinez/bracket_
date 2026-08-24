"""
Cliente de la API del backend.

Un solo lugar que sabe cómo hablarle: el resto del frontend pide datos y
no arma URLs ni maneja códigos HTTP. Si cambia la dirección del backend o
hay que agregar autenticación, se toca acá y nada más.
"""
import requests

from config import Config


class ErrorDeApi(Exception):
    """Algo salió mal del lado del backend. Trae el mensaje que el backend
    haya dado, para poder mostrárselo a quien esté usando la aplicación en
    vez de un error genérico."""


def get(ruta, **params):
    return _pedir("GET", ruta, params=params)


def post(ruta, datos):
    return _pedir("POST", ruta, json=datos)


def put(ruta, datos):
    return _pedir("PUT", ruta, json=datos)


def subir_archivo(ruta, archivo, campos=None):
    """Manda un archivo al backend.

    Va aparte de post() porque un archivo no viaja como JSON: se manda
    como formulario, que es lo que permite transmitirlo tal cual sin
    codificarlo ni cargarlo entero en memoria."""
    return _pedir(
        "POST", ruta,
        files={"imagen": (archivo.filename, archivo.stream, archivo.mimetype)},
        data=campos or {},
    )


def delete(ruta):
    return _pedir("DELETE", ruta)


def _pedir(metodo, ruta, **kwargs):
    respuesta = requests.request(metodo, f"{Config.API_BASE_URL}{ruta}", timeout=10, **kwargs)

    if respuesta.status_code >= 400:
        # El backend devuelve el motivo en el cuerpo. Se lo rescata para
        # poder decir "ya hay un torneo sin finalizar" en vez de "error 400".
        try:
            mensaje = respuesta.json().get("error", "")
        except ValueError:
            mensaje = ""
        raise ErrorDeApi(mensaje or f"El servidor respondió {respuesta.status_code}")

    # 204 significa que salió bien y no hay cuerpo que leer.
    if respuesta.status_code == 204 or not respuesta.content:
        return None
    return respuesta.json()
