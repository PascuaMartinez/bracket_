"""
Configuración del sistema.

El nombre del club, los textos de las pantallas informativas y qué
estadísticas se muestran.
"""
from repositories import configuracion_repository

# Las estadísticas que se pueden ocultar, con su nombre visible.
#
# El catálogo vive acá y no en la base porque no son datos: son las
# estadísticas que el código sabe calcular. Tenerlas en la base
# permitiría agregar una fila para una estadística que no existe, o que
# alguien renombre una clave y rompa el vínculo silenciosamente.
ESTADISTICAS = [
    {"clave": "jugador.rival_mas_frecuente", "nombre": "Con quién jugó más",
     "grupo": "Jugador"},
    {"clave": "jugador.a_quien_le_gano_mas", "nombre": "A quién le ganó más",
     "grupo": "Jugador"},
    {"clave": "jugador.contra_quien_perdio_mas", "nombre": "Contra quién perdió más",
     "grupo": "Jugador"},
    {"clave": "jugador.matchup_mas_parejo", "nombre": "Matchup más parejo",
     "grupo": "Jugador"},
    {"clave": "jugador.mejor_racha", "nombre": "Mejor racha", "grupo": "Jugador"},
    {"clave": "jugador.peor_racha", "nombre": "Peor racha de derrotas", "grupo": "Jugador"},
    {"clave": "jugador.barridas_a_favor", "nombre": "Barridas a favor", "grupo": "Jugador"},
    {"clave": "jugador.barridas_en_contra", "nombre": "Barridas en contra", "grupo": "Jugador"},
    {"clave": "jugador.partidos_cerrados", "nombre": "Partidos cerrados", "grupo": "Jugador"},
    {"clave": "jugador.mejor_puesto", "nombre": "Mejor resultado", "grupo": "Jugador"},
    {"clave": "jugador.primer_torneo", "nombre": "Primer torneo", "grupo": "Jugador"},
    {"clave": "jugador.ultimo_torneo", "nombre": "Último torneo", "grupo": "Jugador"},
    {"clave": "peleador.mas_usado_por", "nombre": "Quién lo usa más",
     "grupo": "Personaje"},
    {"clave": "peleador.peor_enemigo", "nombre": "Su peor enemigo",
     "grupo": "Personaje"},
    {"clave": "peleador.victima_favorita", "nombre": "Su víctima favorita",
     "grupo": "Personaje"},
    {"clave": "peleador.espejos", "nombre": "Espejos", "grupo": "Personaje"},
    {"clave": "peleador.barridas_a_favor", "nombre": "Barridas a favor",
     "grupo": "Personaje"},
    {"clave": "peleador.barridas_en_contra", "nombre": "Barridas en contra",
     "grupo": "Personaje"},
    {"clave": "peleador.partidos_cerrados", "nombre": "Partidos cerrados",
     "grupo": "Personaje"},
]

CLAVES_VALIDAS = {e["clave"] for e in ESTADISTICAS}


class ConfiguracionInvalidaError(Exception):
    pass


def obtener():
    configuracion = configuracion_repository.obtener()
    configuracion["estadisticas_ocultas"] = sorted(
        configuracion_repository.obtener_ocultas()
    )
    return configuracion


def actualizar(nombre_club, texto_inicio=None, texto_formatos=None):
    if not nombre_club or not nombre_club.strip():
        raise ConfiguracionInvalidaError("El nombre del club es obligatorio")

    configuracion_repository.actualizar(
        nombre_club.strip(),
        (texto_inicio or "").strip() or None,
        (texto_formatos or "").strip() or None,
    )
    return obtener()


def guardar_estadisticas_ocultas(claves):
    """
    Guarda qué estadísticas esconder.

    Se validan contra el catálogo: una clave que no corresponde a ninguna
    estadística conocida quedaría guardada para siempre sin efecto, y
    nadie se enteraría de que está mal escrita.
    """
    claves = set(claves or [])
    desconocidas = claves - CLAVES_VALIDAS
    if desconocidas:
        raise ConfiguracionInvalidaError(
            f"Estadísticas desconocidas: {', '.join(sorted(desconocidas))}"
        )

    configuracion_repository.guardar_ocultas(claves)
    return sorted(claves)


def listar_estadisticas():
    """El catálogo con el estado de cada una, para la pantalla de
    configuración."""
    ocultas = configuracion_repository.obtener_ocultas()
    return [{**e, "visible": e["clave"] not in ocultas} for e in ESTADISTICAS]


def filtrar_ocultas(datos, prefijo):
    """
    Saca de un resultado las estadísticas que están ocultas.

    Se filtra al devolver y no al calcular: calcular todo y esconder
    algunas cuesta lo mismo, y permite que volver a mostrar una sea
    inmediato en vez de tener que recalcular el historial.
    """
    ocultas = configuracion_repository.obtener_ocultas()
    return {
        clave: valor for clave, valor in datos.items()
        if f"{prefijo}.{clave}" not in ocultas
    }
