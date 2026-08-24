"""
Exportación del resultado de un torneo como imagen.

Existe porque compartir un torneo en un chat funciona mejor con una
imagen que con un link: se ve en la conversación, sin que nadie tenga que
salir a abrir una página.

La imagen se genera al momento y no se guarda: es un derivado de datos
que ya están, y guardarla obligaría a regenerarla cada vez que se corrige
un resultado -- con el riesgo de que quede una versión vieja dando
vueltas.
"""
import io

from PIL import Image, ImageDraw, ImageFont

from services import tabla_service, torneo_service

# Los mismos colores que la interfaz: una imagen que se ve distinta de la
# aplicación de la que salió no se reconoce como parte de lo mismo.
PAPEL = (247, 247, 245)
TINTA = (28, 31, 38)
GRAFITO = (90, 100, 114)
PINO = (47, 93, 80)
LINEA = (221, 220, 215)

ANCHO = 900
MARGEN = 56
ALTO_FILA = 46


def generar(torneo_id):
    """Devuelve la imagen en memoria, lista para servir."""
    torneo = torneo_service.obtener_torneo(torneo_id)
    tabla = tabla_service.calcular_tabla(torneo_id)

    # El alto depende de cuántos jugadores haya: fijarlo dejaría imágenes
    # con mucho espacio vacío o con la tabla cortada.
    alto = 200 + len(tabla) * ALTO_FILA + 90
    imagen = Image.new("RGB", (ANCHO, alto), PAPEL)
    dibujo = ImageDraw.Draw(imagen)

    y = _dibujar_encabezado(dibujo, torneo)
    y = _dibujar_tabla(dibujo, tabla, y)
    _dibujar_pie(dibujo, y, alto)

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _fuente(tamano, negrita=False):
    """
    Busca una tipografía del sistema, y si no hay usa la que trae Pillow.

    El respaldo importa: sin él, la exportación fallaría entera en
    cualquier máquina donde no estén esas fuentes -- que es casi cualquier
    servidor. Es preferible una imagen con una tipografía fea a un error.
    """
    candidatas = [
        "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if negrita else ""),
    ]
    for nombre in candidatas:
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def _dibujar_encabezado(dibujo, torneo):
    y = MARGEN

    subtitulo = f"{_nombre_formato(torneo['modo'])} · {torneo['fecha']}"
    if torneo.get("lugar"):
        subtitulo += f" · {torneo['lugar']}"
    dibujo.text((MARGEN, y), subtitulo.upper(), font=_fuente(14), fill=PINO)
    y += 26

    dibujo.text((MARGEN, y), torneo["nombre"], font=_fuente(38, negrita=True), fill=TINTA)
    y += 54

    # La línea de separación: el mismo recurso gráfico que la interfaz usa
    # para dividir secciones.
    dibujo.line([(MARGEN, y), (ANCHO - MARGEN, y)], fill=TINTA, width=2)
    return y + 28


def _dibujar_tabla(dibujo, tabla, y):
    columnas = {"puesto": MARGEN, "nombre": MARGEN + 60,
                "pj": ANCHO - 300, "pg": ANCHO - 230, "pp": ANCHO - 160,
                "wr": ANCHO - 90}

    fuente_encabezado = _fuente(12)
    for etiqueta, clave in (("#", "puesto"), ("JUGADOR", "nombre"),
                            ("PJ", "pj"), ("PG", "pg"), ("PP", "pp"), ("WR", "wr")):
        dibujo.text((columnas[clave], y), etiqueta, font=fuente_encabezado, fill=GRAFITO)
    y += 22
    dibujo.line([(MARGEN, y), (ANCHO - MARGEN, y)], fill=LINEA, width=1)
    y += 10

    for indice, fila in enumerate(tabla):
        # El campeón en el color de acento: en una imagen que se mira de
        # reojo en un chat, quién ganó tiene que saltar a la vista.
        es_campeon = fila.get("puesto") == 1
        color = PINO if es_campeon else TINTA
        fuente = _fuente(17, negrita=es_campeon)

        dibujo.text((columnas["puesto"], y), str(fila.get("puesto", "-")),
                    font=fuente, fill=color)
        dibujo.text((columnas["nombre"], y), fila["nombre"], font=fuente, fill=color)

        fuente_dato = _fuente(15)
        dibujo.text((columnas["pj"], y), str(fila.get("pj", 0)), font=fuente_dato, fill=GRAFITO)
        dibujo.text((columnas["pg"], y), str(fila.get("pg", 0)), font=fuente_dato, fill=GRAFITO)
        dibujo.text((columnas["pp"], y), str(fila.get("pp", 0)), font=fuente_dato, fill=GRAFITO)
        dibujo.text((columnas["wr"], y), f"{round(fila.get('win_rate', 0) * 100)}%",
                    font=fuente_dato, fill=GRAFITO)

        y += ALTO_FILA
        if indice < len(tabla) - 1:
            dibujo.line([(MARGEN, y - 12), (ANCHO - MARGEN, y - 12)], fill=LINEA, width=1)

    return y


def _dibujar_pie(dibujo, y, alto):
    dibujo.text((MARGEN, alto - 46), "Generado con Bracket", font=_fuente(13), fill=GRAFITO)


def _nombre_formato(modo):
    nombres = {
        "todos_contra_todos": "Todos contra todos",
        "eliminacion": "Eliminación directa",
        "rey_de_la_cancha": "Rey de la cancha",
        "grupos_eliminacion": "Grupos + eliminación",
    }
    return nombres.get(modo, (modo or "").replace("_", " "))
