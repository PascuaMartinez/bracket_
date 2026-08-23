"""
Mide cuántas consultas hace cada pantalla.

    python medir.py

Sirve para saber qué optimizar antes de optimizar, y para comprobar
después que el cambio sirvió de algo.
"""
from database.medicion import contador
from services import (
    estadisticas_service, tabla_historica_service, tabla_service, torneo_service,
)


def medir(nombre, operacion):
    with contador() as c:
        try:
            operacion()
        except Exception as e:
            print(f"{nombre:38s} error: {e}")
            return
    print(f"{nombre:38s} {c.total:5d} consultas")
    # Las consultas que más se repiten suelen delatar el problema: si una
    # aparece 40 veces, es que está adentro de un bucle.
    for consulta, veces in c.resumen(3):
        if veces > 1:
            print(f"{'':40s} {veces:3d}x  {consulta[:60]}")


def main():
    torneos = torneo_service.listar_torneos()
    jugadores = [j["id"] for j in __import__("services.jugador_service",
                                             fromlist=["x"]).listar_jugadores()]

    print("Consultas por operación\n")
    medir("Listar torneos", torneo_service.listar_torneos)

    if torneos:
        torneo_id = torneos[0]["id"]
        medir("Tabla de un torneo", lambda: tabla_service.calcular_tabla(torneo_id))

    medir("Tabla histórica", tabla_historica_service.calcular_tabla_historica)

    if jugadores:
        medir("Estadísticas de un jugador",
              lambda: estadisticas_service.obtener_estadisticas(jugadores[0]))


if __name__ == "__main__":
    main()
