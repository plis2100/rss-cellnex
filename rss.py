import html
import re
import urllib.request
import xml.etree.ElementTree as ET

from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

WEB_URL = (
    "https://www.cellnex.com/es-es/"
    "sala-de-prensa/noticias/"
)

OUTPUT_FILE = Path("cellnex.xml")

MESES = {
    "Ene": 1,
    "Feb": 2,
    "Mar": 3,
    "Abr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Ago": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dic": 12,
}


def limpiar_texto(texto):
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = html.unescape(texto)
    return " ".join(texto.split())


def descargar_noticias():
    solicitud = urllib.request.Request(
        WEB_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
            "Accept": "text/html",
        },
    )

    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        contenido = respuesta.read().decode(
            "utf-8",
            errors="replace",
        )

    patron_titulos = re.compile(
        r'<a\s+href="([^"]+)"[^>]*>\s*'
        r'<h4\s+class="post-title"[^>]*>(.*?)</h4>',
        re.IGNORECASE | re.DOTALL,
    )

    patron_fechas = re.compile(
        r'<li\s+class="post-date"[^>]*>(.*?)</li>',
        re.IGNORECASE | re.DOTALL,
    )

    patron_categorias = re.compile(
        r'<li\s+class="post-category"[^>]*>(.*?)</li>',
        re.IGNORECASE | re.DOTALL,
    )

    patron_resumenes = re.compile(
        r'<p\s+class="post-excerpt"[^>]*>(.*?)</p>',
        re.IGNORECASE | re.DOTALL,
    )

    titulos = patron_titulos.findall(contenido)
    fechas = patron_fechas.findall(contenido)
    categorias = patron_categorias.findall(contenido)
    resumenes = patron_resumenes.findall(contenido)

    noticias = []
    enlaces_encontrados = set()

    for posicion, (enlace, titulo) in enumerate(titulos):
        enlace = html.unescape(enlace)
        titulo = limpiar_texto(titulo)

        if (
            not enlace.startswith("https://www.cellnex.com/")
            or enlace in enlaces_encontrados
        ):
            continue

        fecha = ""

        if posicion < len(fechas):
            fecha = limpiar_texto(fechas[posicion])

        categoria = ""

        if posicion < len(categorias):
            categoria = limpiar_texto(categorias[posicion])

        resumen = titulo

        if posicion < len(resumenes):
            resumen = limpiar_texto(resumenes[posicion])

        enlaces_encontrados.add(enlace)

        noticias.append(
            {
                "titulo": titulo,
                "enlace": enlace,
                "fecha": fecha,
                "categoria": categoria,
                "resumen": resumen,
            }
        )

    return noticias


def convertir_fecha(fecha):
    partes = fecha.split()

    if len(partes) != 3:
        return None

    dia = int(partes[0])
    mes = MESES.get(partes[1])
    anio = int(partes[2])

    if not mes:
        return None

    return datetime(
        anio,
        mes,
        dia,
        tzinfo=timezone.utc,
    )


def crear_rss(noticias):
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        },
    )

    canal = ET.SubElement(rss, "channel")

    ET.SubElement(canal, "title").text = "Noticias de Cellnex"
    ET.SubElement(canal, "link").text = WEB_URL
    ET.SubElement(canal, "description").text = (
        "Últimas noticias publicadas por Cellnex"
    )
    ET.SubElement(canal, "language").text = "es"
    ET.SubElement(canal, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    enlace_atom = ET.SubElement(
        canal,
        "{http://www.w3.org/2005/Atom}link",
    )
    enlace_atom.set("href", WEB_URL)
    enlace_atom.set("rel", "self")
    enlace_atom.set("type", "application/rss+xml")

    for noticia in noticias:
        elemento = ET.SubElement(canal, "item")

        ET.SubElement(elemento, "title").text = noticia["titulo"]
        ET.SubElement(elemento, "link").text = noticia["enlace"]
        ET.SubElement(elemento, "description").text = noticia["resumen"]

        identificador = ET.SubElement(elemento, "guid")
        identificador.set("isPermaLink", "true")
        identificador.text = noticia["enlace"]

        if noticia["categoria"]:
            ET.SubElement(
                elemento,
                "category",
            ).text = noticia["categoria"]

        if noticia["fecha"]:
            try:
                fecha_publicacion = convertir_fecha(
                    noticia["fecha"]
                )

                if fecha_publicacion:
                    ET.SubElement(
                        elemento,
                        "pubDate",
                    ).text = format_datetime(fecha_publicacion)
            except (ValueError, TypeError):
                pass

    ET.indent(rss, space="  ")

    ET.ElementTree(rss).write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )


def main():
    noticias = descargar_noticias()

    if not noticias:
        raise RuntimeError(
            "No se encontraron noticias en la web de Cellnex"
        )

    crear_rss(noticias)

    print(
        f"RSS creada correctamente con "
        f"{len(noticias)} noticias"
    )


if __name__ == "__main__":
    main()
