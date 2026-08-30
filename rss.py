import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

RSS_OFICIAL = (
    "https://www.cellnex.com/es-es/"
    "sala-de-prensa/noticias/feed/"
)

ARCHIVO_SALIDA = Path("cellnex.xml")


def descargar_rss():
    solicitud = urllib.request.Request(
        RSS_OFICIAL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml",
        },
    )

    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        contenido = respuesta.read()

    # Comprueba que Cellnex ha devuelto realmente una RSS válida.
    raiz = ET.fromstring(contenido)

    if raiz.tag.lower().split("}")[-1] != "rss":
        raise RuntimeError("Cellnex no ha devuelto una RSS válida")

    elementos = raiz.findall(".//item")

    if not elementos:
        raise RuntimeError("La RSS de Cellnex no contiene noticias")

    ARCHIVO_SALIDA.write_bytes(contenido)

    print(
        f"RSS creada correctamente con "
        f"{len(elementos)} noticias"
    )


if __name__ == "__main__":
    descargar_rss()
