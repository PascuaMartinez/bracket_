"""
Cache de resultados calculados.

La tabla histórica recorre todos los torneos y recalcula todas sus tablas
en cada visita. El commit anterior bajó las consultas de 151 a 3, pero
esas 3 se repiten cada vez que alguien entra, y el cálculo también.

Como los datos solo cambian cuando se carga un resultado -- algo que pasa
unas pocas veces por noche de torneo, no cientos por minuto -- guardar lo
calculado y reusarlo hasta la próxima escritura es un intercambio muy
favorable.

Es un cache en memoria del proceso, a propósito: sumar Redis o similar
para esto sería agregar una pieza de infraestructura para un problema que
no la necesita. La contra es que con varios procesos cada uno tendría su
copia, y una escritura en uno no invalidaría la del otro. Eso está
documentado en el README junto con el requisito de correr con un solo
proceso.
"""
import threading
import time

# Cuánto vale un resultado guardado. No es para que los datos estén al
# día -- de eso se encarga la invalidación al escribir -- sino como red de
# seguridad: si alguna escritura no invalidara por un error, el cache se
# vacía solo en vez de quedar mintiendo para siempre.
SEGUNDOS_DE_VIDA = 300

_guardado = {}
# Las escrituras pueden llegar mientras otro hilo está leyendo, así que
# el acceso va protegido.
_candado = threading.Lock()


def obtener(clave, calcular):
    """
    Devuelve lo guardado bajo esa clave, o lo calcula y lo guarda.

    calcular es una función sin argumentos: se la pasa así, y no el
    resultado ya hecho, para que no se calcule cuando hay algo guardado.
    """
    with _candado:
        entrada = _guardado.get(clave)
        if entrada is not None:
            valor, guardado_en = entrada
            if time.time() - guardado_en < SEGUNDOS_DE_VIDA:
                return valor

    # El cálculo va FUERA del candado: puede tardar, y bloquear a todos
    # los demás mientras tanto anularía el beneficio. Como consecuencia,
    # dos pedidos simultáneos pueden calcular lo mismo dos veces la
    # primera vez. Es aceptable: cuesta un cálculo de más y evita que una
    # consulta lenta deje la aplicación entera esperando.
    valor = calcular()

    with _candado:
        _guardado[clave] = (valor, time.time())
    return valor


def invalidar_todo():
    """
    Vacía el cache entero.

    Se vacía todo y no solo lo que cambió porque los resultados están
    encadenados: cargar un partido cambia la tabla de ese torneo, que
    cambia el histórico, que cambia las estadísticas de cada jugador que
    participó. Rastrear esas dependencias sería complejo y fácil de
    equivocar; vaciar todo cuesta un recálculo y no puede quedar
    inconsistente.
    """
    with _candado:
        _guardado.clear()


def estado():
    """Cuántas entradas hay guardadas. Para diagnóstico."""
    with _candado:
        return {"entradas": len(_guardado), "claves": sorted(_guardado.keys())}
