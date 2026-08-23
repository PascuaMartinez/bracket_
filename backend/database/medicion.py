"""
Instrumentación para medir cuántas consultas hace cada operación.

Antes de optimizar hay que saber qué está lento y por qué. La intuición
falla seguido: lo que parece caro suele ser barato, y el problema real
está en algo que se repite muchas veces sin que se note.

Se cuenta la cantidad de consultas y no el tiempo porque el tiempo
depende de la máquina, de la red y de qué más esté corriendo. La cantidad
de consultas es una propiedad del código: si una operación hace 200
consultas donde podría hacer 5, eso está mal en cualquier máquina.

Uso:

    with contador() as c:
        tabla_historica_service.calcular_tabla_historica()
    print(c.total)
"""
import threading
from contextlib import contextmanager

# El contador vive por hilo: dos operaciones en paralelo no se mezclan.
_local = threading.local()


class Contador:
    def __init__(self):
        self.total = 0
        self.por_consulta = {}

    def registrar(self, consulta):
        self.total += 1
        # Se guarda solo el principio de la consulta: alcanza para
        # identificarla y evita llenar la salida con listas de columnas.
        clave = " ".join(consulta.split())[:80]
        self.por_consulta[clave] = self.por_consulta.get(clave, 0) + 1

    def resumen(self, cuantas=10):
        """Las consultas más repetidas, que son las que suelen delatar el
        problema."""
        ordenadas = sorted(self.por_consulta.items(), key=lambda x: -x[1])
        return ordenadas[:cuantas]


@contextmanager
def contador():
    c = Contador()
    _local.contador = c
    try:
        yield c
    finally:
        _local.contador = None


def registrar(consulta):
    """La llama la capa de datos en cada consulta. Fuera de una medición
    no hace nada, así que no cuesta nada dejarla puesta."""
    c = getattr(_local, "contador", None)
    if c is not None:
        c.registrar(consulta)
