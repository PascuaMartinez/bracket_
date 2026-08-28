"""
Prueba de que el borrado de un torneo limpia todo lo que cuelga de él.

Ya pasó dos veces que se agregara una tabla nueva y el borrado quedara
viejo: el síntoma es un error de clave foránea al borrar, lejos de donde
se hizo el cambio. Esta prueba lo detecta en el momento.
"""
import re
from pathlib import Path


def test_el_borrado_limpia_todas_las_tablas_que_cuelgan_del_torneo():
    """
    Se comparan las tablas del esquema que referencian a torneo o a
    torneo_jugador contra las que el borrado toca.

    Se lee el esquema en vez de listar las tablas a mano: una lista escrita
    acá tendría el mismo problema que se quiere evitar -- quedar vieja
    cuando se agregue la próxima.
    """
    raiz = Path(__file__).resolve().parent.parent.parent
    esquema = (raiz / "schema.sql").read_text(encoding="utf-8")
    repositorio = (raiz / "backend" / "repositories" / "torneo_repository.py").read_text(
        encoding="utf-8"
    )

    # Las tablas que dependen del torneo, directa o indirectamente.
    dependientes = set()
    for bloque in esquema.split("CREATE TABLE ")[1:]:
        nombre = bloque.split("(")[0].strip()
        if nombre == "torneo":
            continue
        if re.search(r"REFERENCES\s+(torneo|torneo_jugador)\s*\(", bloque):
            dependientes.add(nombre)

    borrado = repositorio[repositorio.index("def eliminar(torneo_id)"):]
    borrado = borrado[: borrado.index("\ndef ")] if "\ndef " in borrado else borrado

    faltantes = [tabla for tabla in dependientes if tabla not in borrado]

    assert not faltantes, (
        f"El borrado de un torneo no limpia: {', '.join(sorted(faltantes))}. "
        "Cada tabla que cuelgue de un torneo tiene que borrarse ahí, o la "
        "clave foránea va a impedir borrar el torneo."
    )
