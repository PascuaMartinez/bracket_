"""
Guardado de imágenes.

Las imágenes se guardan en disco y en la base va solo la ruta. Meter
archivos binarios en la base infla los backups, hace que cada lectura de
un jugador arrastre la foto aunque no se vaya a mostrar, y desaprovecha
que un servidor web sirve archivos estáticos mucho mejor que una consulta
SQL.

La función que guarda está aislada a propósito: si mañana hay que subir
las imágenes a un servicio en la nube -- necesario en cualquier hosting
donde el disco se borra al reiniciar -- se cambia acá y ninguna otra
parte del proyecto se entera.
"""
import os
import uuid

from werkzeug.utils import secure_filename

# Solo formatos de imagen conocidos. Aceptar cualquier extensión
# permitiría subir un archivo ejecutable y dejarlo servido desde el
# servidor, que es una forma clásica de comprometer un sitio.
EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Un límite razonable para una foto de perfil. Sin límite, una imagen de
# 50 MB llenaría el disco y haría lentísima cada página que la muestre.
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024

CARPETA_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")


class ImagenInvalidaError(Exception):
    pass


def guardar(archivo, carpeta):
    """
    Guarda el archivo y devuelve la ruta que va a la base.

    carpeta separa por tipo ('jugadores', 'peleadores') para que la
    carpeta de subidas no termine siendo una pila de miles de archivos
    sueltos.
    """
    if archivo is None or not archivo.filename:
        return None

    extension = os.path.splitext(secure_filename(archivo.filename))[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ImagenInvalidaError(
            f"Formato no permitido. Se aceptan: {', '.join(sorted(EXTENSIONES_PERMITIDAS))}"
        )

    _verificar_tamano(archivo)

    # El nombre se genera y no se reusa el original. Dos personas subiendo
    # "foto.png" se pisarían una a la otra, y un nombre venido de afuera
    # puede traer caracteres que sirvan para escapar de la carpeta.
    nombre = f"{uuid.uuid4().hex}{extension}"

    destino = os.path.join(CARPETA_BASE, carpeta)
    os.makedirs(destino, exist_ok=True)
    archivo.save(os.path.join(destino, nombre))

    # Se guarda la ruta relativa: la absoluta cambiaría al mover el
    # proyecto de máquina y dejaría todas las imágenes rotas.
    return f"uploads/{carpeta}/{nombre}"


def eliminar(ruta):
    """Borra el archivo, si existe.

    No falla si no está: puede haberse borrado a mano, o la base puede
    tener una ruta vieja. Que borrar algo que ya no está sea un error no
    aportaría nada."""
    if not ruta:
        return
    completa = os.path.join(os.path.dirname(CARPETA_BASE), ruta)
    if os.path.isfile(completa):
        os.remove(completa)


def _verificar_tamano(archivo):
    """Mide el archivo sin cargarlo entero en memoria: se va al final para
    ver la posición y se vuelve al principio."""
    archivo.seek(0, os.SEEK_END)
    tamano = archivo.tell()
    archivo.seek(0)

    if tamano > TAMANO_MAXIMO_BYTES:
        megas = TAMANO_MAXIMO_BYTES // (1024 * 1024)
        raise ImagenInvalidaError(f"La imagen no puede pesar más de {megas} MB")
