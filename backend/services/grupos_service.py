"""
Armado de la fase de grupos.

Dos problemas: repartir los jugadores en grupos, y decidir cuántos
clasifican de cada uno cuando los cupos no se dividen parejo.
"""


def repartir_en_grupos(jugadores_ids, cantidad_grupos):
    """
    Reparte a los jugadores en grupos lo más parejo posible.

    Se reparte en zigzag y no por bloques: el primero al grupo A, el
    segundo al B, y cuando se llega al último se vuelve para atrás. Si la
    lista viene ordenada por nivel -- por ejemplo, según la tabla
    histórica -- repartir por bloques dejaría a todos los mejores juntos
    en el grupo A, y ese grupo eliminaría entre sí a gente que en otro
    hubiera clasificado.

    Con el zigzag, cada grupo recibe uno de los mejores, uno de los
    siguientes, y así: quedan equilibrados.
    """
    grupos = [[] for _ in range(cantidad_grupos)]

    indice = 0
    yendo_hacia_adelante = True
    for jugador_id in jugadores_ids:
        grupos[indice].append(jugador_id)

        if yendo_hacia_adelante:
            if indice == cantidad_grupos - 1:
                yendo_hacia_adelante = False   # rebota en el último
            else:
                indice += 1
        else:
            if indice == 0:
                yendo_hacia_adelante = True    # rebota en el primero
            else:
                indice -= 1

    return grupos


def repartir_cupos(cupos_totales, tamanos_de_grupo):
    """
    Cuántos clasifican de cada grupo.

    El caso simple es que los cupos se dividan parejo: 4 cupos en 2 grupos
    son 2 y 2. El interesante es cuando no: 5 cupos en 2 grupos podrían
    ser 3 y 2, pero ¿cuál se queda con el tercero?

    Se usa el método del resto mayor: se reparte la parte entera a todos y
    los cupos sobrantes van a los grupos más grandes. La razón es que en
    un grupo de 5 clasificar es más difícil que en uno de 4 -- hay más
    rivales por el mismo lugar -- así que el cupo extra corresponde ahí.
    Repartirlo por orden de grupo sería arbitrario, y sortearlo haría que
    el mismo torneo dé resultados distintos cada vez.

    Devuelve una lista con cuántos pasan de cada grupo, en el mismo orden.
    """
    cantidad_grupos = len(tamanos_de_grupo)
    if cantidad_grupos == 0:
        return []

    base = cupos_totales // cantidad_grupos
    sobrantes = cupos_totales % cantidad_grupos

    # Los grupos más grandes primero. El índice se lleva al costado para
    # poder devolver el resultado en el orden original.
    por_tamano = sorted(range(cantidad_grupos),
                        key=lambda i: -tamanos_de_grupo[i])

    cupos = [base] * cantidad_grupos
    for posicion in range(sobrantes):
        cupos[por_tamano[posicion]] += 1

    # Nadie puede clasificar más gente de la que tiene. Si pasara, el cupo
    # sobrante se pierde en vez de inventar clasificados.
    return [min(cupos[i], tamanos_de_grupo[i]) for i in range(cantidad_grupos)]


def nombre_de_grupo(indice):
    """Grupo A, B, C... Más allá de la Z vuelve a números, que es mejor
    que empezar a combinar letras."""
    if indice < 26:
        return f"Grupo {chr(ord('A') + indice)}"
    return f"Grupo {indice + 1}"
