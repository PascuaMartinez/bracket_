"""
Crea el primer usuario administrador.

Va como script y no como endpoint a propósito: un endpoint público para
crear administradores le permitiría a cualquiera darse de alta. Esto se
corre desde la máquina donde vive el proyecto, que es la garantía de que
quien lo hace tiene acceso legítimo.

    python crear_usuario.py
"""
import getpass
import sys

from services import usuario_service


def main():
    print("Crear usuario administrador\n")
    nombre = input("Usuario: ").strip()
    # getpass no muestra lo que se escribe: una contraseña visible en la
    # terminal queda en el historial de la sesión y a la vista de quien
    # pase por atrás.
    password = getpass.getpass("Contraseña: ")
    repetida = getpass.getpass("Repetir contraseña: ")

    if password != repetida:
        print("\nLas contraseñas no coinciden.")
        return 1

    try:
        usuario_service.crear_usuario(nombre, password)
    except usuario_service.UsuarioInvalidoError as e:
        print(f"\n{e}")
        return 1

    print(f"\nUsuario '{nombre}' creado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
