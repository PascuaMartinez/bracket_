"""Pruebas de la detección de empates en el corte de clasificación."""
from services.grupos_service import detectar_empate_en_el_corte


def fila(nombre, puntos):
    return {"nombre": nombre, "puntos": puntos, "jugador_id": abs(hash(nombre)) % 100}


def test_sin_empate_no_hay_nada_que_resolver():
    tabla = [fila("Ana", 3), fila("Beto", 2), fila("Caro", 1)]

    assert detectar_empate_en_el_corte(tabla, cupos=2) is None


def test_detecta_el_empate_justo_en_la_linea():
    """El segundo y el tercero empatan, y solo pasa uno."""
    tabla = [fila("Ana", 3), fila("Beto", 2), fila("Caro", 2)]

    empate = detectar_empate_en_el_corte(tabla, cupos=2)

    assert [e["nombre"] for e in empate["empatados"]] == ["Beto", "Caro"]
    assert empate["lugares_en_disputa"] == 1


def test_devuelve_el_bloque_completo_de_empatados():
    """Si empatan tres por dos lugares, resolver entre dos dejaría afuera
    al tercero que tenía el mismo derecho."""
    tabla = [fila("Ana", 3), fila("Beto", 2), fila("Caro", 2), fila("Dan", 2)]

    empate = detectar_empate_en_el_corte(tabla, cupos=3)

    assert len(empate["empatados"]) == 3
    assert empate["lugares_en_disputa"] == 2


def test_un_empate_arriba_del_corte_no_importa():
    """Los dos primeros empatan pero los dos pasan igual: no hay disputa."""
    tabla = [fila("Ana", 3), fila("Beto", 3), fila("Caro", 1)]

    assert detectar_empate_en_el_corte(tabla, cupos=2) is None


def test_si_clasifican_todos_no_hay_corte():
    tabla = [fila("Ana", 2), fila("Beto", 2)]

    assert detectar_empate_en_el_corte(tabla, cupos=2) is None


def test_si_no_clasifica_nadie_tampoco():
    tabla = [fila("Ana", 2), fila("Beto", 2)]

    assert detectar_empate_en_el_corte(tabla, cupos=0) is None
