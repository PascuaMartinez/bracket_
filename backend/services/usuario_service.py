"""
Autenticación.

Las contraseñas se guardan como hash y nunca en claro. Se usa el hash de
Werkzeug (PBKDF2 con sal), que ya viene con Flask: no hace falta sumar
una dependencia, y escribir el hasheo a mano es de las peores ideas
posibles en seguridad.
"""
from werkzeug.security import check_password_hash, generate_password_hash

from repositories import usuario_repository

# Una contraseña corta se rompe por fuerza bruta en poco tiempo. No es un
# número mágico: es el mínimo por debajo del cual la protección deja de
# tener sentido.
LARGO_MINIMO_PASSWORD = 8


class CredencialesInvalidasError(Exception):
    pass


class UsuarioInvalidoError(Exception):
    pass


def crear_usuario(nombre_usuario, password):
    if not nombre_usuario or not nombre_usuario.strip():
        raise UsuarioInvalidoError("El nombre de usuario es obligatorio")

    if not password or len(password) < LARGO_MINIMO_PASSWORD:
        raise UsuarioInvalidoError(
            f"La contraseña tiene que tener al menos {LARGO_MINIMO_PASSWORD} caracteres"
        )

    nombre_usuario = nombre_usuario.strip()
    if usuario_repository.obtener_por_nombre(nombre_usuario) is not None:
        raise UsuarioInvalidoError(f"Ya existe el usuario '{nombre_usuario}'")

    return usuario_repository.crear(nombre_usuario, generate_password_hash(password))


def verificar(nombre_usuario, password):
    """Devuelve el nombre de usuario si las credenciales son correctas.

    El mensaje de error es el mismo tanto si el usuario no existe como si
    la contraseña está mal. Distinguirlos le confirmaría a un atacante qué
    nombres de usuario son válidos, que es justo la mitad del trabajo.
    """
    usuario = usuario_repository.obtener_por_nombre((nombre_usuario or "").strip())

    if usuario is None or not check_password_hash(usuario["password_hash"], password or ""):
        raise CredencialesInvalidasError("Usuario o contraseña incorrectos")

    return usuario["nombre_usuario"]


def hay_usuarios():
    return usuario_repository.contar() > 0
