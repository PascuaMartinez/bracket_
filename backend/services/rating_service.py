"""
Rating de jugadores por el modelo Bradley-Terry.

El win rate no alcanza para comparar. Alguien con 80% que solo jugó
contra los más flojos no necesariamente es mejor que otro con 55% que
enfrentó siempre a los más fuertes: el win rate mide cuánto ganaste, no
contra quién.

Bradley-Terry resuelve eso. Le asigna a cada jugador un número -- su
fuerza -- y postula que la probabilidad de que A le gane a B es:

    P(A gana) = fuerza(A) / (fuerza(A) + fuerza(B))

Las fuerzas no se conocen: se estiman buscando los valores que hagan más
probable el historial que efectivamente ocurrió. Ganarle a alguien fuerte
sube más el rating que ganarle a alguien flojo, porque para explicar esa
victoria el modelo necesita atribuirte más fuerza.

Se resuelve con el algoritmo iterativo estándar para este modelo: se
arranca con todos iguales y se ajusta cada fuerza según a quién enfrentó,
repitiendo hasta que los valores dejan de moverse.
"""
import math

# Cuántas veces ajustar antes de rendirse. El algoritmo converge rápido
# con pocos jugadores, pero un tope evita que un caso patológico deje el
# cálculo girando indefinidamente.
MAXIMO_DE_PASADAS = 200

# Cuándo se considera que los valores dejaron de moverse. Más precisión
# que esta no cambia nada visible: el rating se muestra redondeado.
TOLERANCIA = 1e-6

# Se le suma media victoria y media derrota ficticias a cada
# enfrentamiento posible. Sin esto, un jugador invicto tendría fuerza
# infinita -- el modelo no puede explicar "nunca perdió" con un número
# finito -- y uno que perdió todo tendría fuerza cero. Con pocos partidos,
# que es lo normal en un grupo de amigos, ese caso aparece seguido.
SUAVIZADO = 0.5

# El rating se muestra centrado en 1000, como es habitual en sistemas de
# puntuación: números redondos y fáciles de comparar entre sí.
RATING_BASE = 1000
ESCALA = 400


def calcular_ratings(jugadores_ids, partidos):
    """
    Estima la fuerza de cada jugador a partir de sus resultados.

    partidos es una lista de (ganador_id, perdedor_id).

    Devuelve {jugador_id: rating}, donde el rating es la fuerza llevada a
    una escala legible. Los jugadores sin partidos quedan en el valor base:
    sin datos no hay nada que estimar, y dejarlos afuera haría que
    desaparezcan de la tabla.
    """
    jugadores = list(jugadores_ids)
    if len(jugadores) < 2:
        return {j: RATING_BASE for j in jugadores}

    victorias, enfrentamientos = _contar(jugadores, partidos)
    fuerzas = _estimar_fuerzas(jugadores, victorias, enfrentamientos)

    return {j: _a_rating(fuerzas[j], fuerzas) for j in jugadores}


def probabilidad(rating_a, rating_b):
    """
    Qué tan probable es que A le gane a B, según sus ratings.

    Es la fórmula del modelo escrita en términos del rating: la diferencia
    entre dos ratings determina la probabilidad, sin importar sus valores
    absolutos. Una diferencia de 400 puntos da alrededor de 10 a 1.
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / ESCALA))


def _contar(jugadores, partidos):
    """Cuántas veces ganó cada uno y cuántas se enfrentó con cada otro."""
    victorias = {j: 0.0 for j in jugadores}
    enfrentamientos = {j: {otro: 0.0 for otro in jugadores if otro != j}
                       for j in jugadores}

    for ganador, perdedor in partidos:
        if ganador not in victorias or perdedor not in victorias:
            continue
        victorias[ganador] += 1
        enfrentamientos[ganador][perdedor] += 1
        enfrentamientos[perdedor][ganador] += 1

    # El suavizado: media victoria y media derrota ficticias contra cada
    # rival posible. Evita las fuerzas infinitas de los invictos.
    for jugador in jugadores:
        for otro in enfrentamientos[jugador]:
            enfrentamientos[jugador][otro] += 2 * SUAVIZADO
        victorias[jugador] += SUAVIZADO * (len(jugadores) - 1)

    return victorias, enfrentamientos


def _estimar_fuerzas(jugadores, victorias, enfrentamientos):
    """
    Busca las fuerzas que mejor explican los resultados.

    En cada pasada, la fuerza de un jugador se recalcula como sus
    victorias divididas por la suma, sobre cada rival, de los
    enfrentamientos ponderados por la fuerza combinada de ambos. Es decir:
    ganar mucho sube la fuerza, pero enfrentar rivales fuertes hace que
    cada victoria pese más.

    Se repite hasta que los valores se estabilizan.
    """
    fuerzas = {j: 1.0 for j in jugadores}

    for _ in range(MAXIMO_DE_PASADAS):
        nuevas = {}
        for jugador in jugadores:
            denominador = sum(
                cantidad / (fuerzas[jugador] + fuerzas[otro])
                for otro, cantidad in enfrentamientos[jugador].items()
                if cantidad > 0
            )
            nuevas[jugador] = victorias[jugador] / denominador if denominador else 1.0

        # Se normaliza en cada pasada. Las fuerzas solo importan por su
        # proporción entre sí -- multiplicarlas todas por dos no cambia
        # ninguna probabilidad -- y sin normalizar crecerían o se
        # achicarían sin parar, hasta perder precisión.
        promedio = sum(nuevas.values()) / len(nuevas)
        nuevas = {j: f / promedio for j, f in nuevas.items()}

        se_movio = max(abs(nuevas[j] - fuerzas[j]) for j in jugadores)
        fuerzas = nuevas
        if se_movio < TOLERANCIA:
            break

    return fuerzas


def _a_rating(fuerza, todas):
    """
    Lleva la fuerza a una escala legible, centrada en 1000.

    La transformación es logarítmica porque las fuerzas son
    multiplicativas: el doble de fuerza tiene que traducirse en una
    diferencia fija de rating, no en el doble de puntos.
    """
    if fuerza <= 0:
        return RATING_BASE
    return round(RATING_BASE + ESCALA * math.log10(fuerza))
