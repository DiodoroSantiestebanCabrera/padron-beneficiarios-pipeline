"""Carga de catálogos oficiales de geografía (INEGI/SEPOMEX).

Módulo compartido: tanto el generador de datos sintéticos como la
resolución real de geografía (silver/geografia.py) dependen de esta
misma lógica de carga -- vive aquí una sola vez para no duplicarla.
"""

from pathlib import Path
from typing import NamedTuple

import pandas as pd

RUTA_CATALOGO_MUNICIPIOS = Path("data/catalogs/claves_municipio.csv")
RUTA_CATALOGO_LOCALIDADES = Path("data/catalogs/claves_localidad.csv")

COLUMNA_CLAVE_MUNICIPIO = "Clave de municipio"
COLUMNA_NOMBRE_MUNICIPIO = "Municipio"
COLUMNA_NOMBRE_LOCALIDAD = "Nombre de la localidad"


class Catalogos(NamedTuple):
    """Agrupa los dos catálogos ya cargados, con nombres explícitos en vez
    de posiciones de tupla sin etiquetar."""

    # list [] = La gran caja ordenada (mutable)
    # tuple () = El par o paquete sellado de exactamente 2 elementos (int y str)
    # Visual: [ (1, "Amaxac"), (2, "Apetatitlán") ]
    municipios: list[tuple[int, str]]

    # dict {} = El diccionario de búsqueda rápida
    # clave (int) : lista de textos (list[str])
    # Visual: { 1: ["La Preciosa", "San Isidro"], 2: ["Belén"] }
    localidades_por_municipio: dict[int, list[str]]


def cargar_catalogos() -> Catalogos:
    """Carga los catálogos oficiales UNA sola vez, en estructuras simples
    de Python (no se vuelve a leer el CSV por cada fila que se procese
    después -- el costo de leer y agrupar se paga una sola vez)."""
    municipios_df = pd.read_csv(RUTA_CATALOGO_MUNICIPIOS, encoding="utf-8-sig")
    localidades_df = pd.read_csv(RUTA_CATALOGO_LOCALIDADES, encoding="utf-8-sig")

    # zip toma múltiples columnas y las alinea fila por fila empaquetándolas en tuplas, mientras que list toma todas esas tuplas y las envuelve en una lista
    lista_municipios = list(
        zip(
            municipios_df[COLUMNA_CLAVE_MUNICIPIO],
            municipios_df[COLUMNA_NOMBRE_MUNICIPIO],
        )
    )

    localidades_por_municipio = {
        # clave_mun es la llave del diccionario que guarda en una lista grupo_mun es la mini-tabla completa(guarda nombre de localidades), y .tolist() extrae una columna específica de ahí y la aplana en una lista
        clave_mun: grupo_mun[COLUMNA_NOMBRE_LOCALIDAD].tolist()
        # for necesita dos elementos del diccionario llave(key) y Valor(valor, o este caso la lista)
        # Cuando en Pandas usamos .groupby() entrega una pareja por cada corte que hace: (La Clave, La Mini-tabla)
        for clave_mun, grupo_mun in localidades_df.groupby(COLUMNA_CLAVE_MUNICIPIO)
    }

    return Catalogos(
        municipios=lista_municipios, localidades_por_municipio=localidades_por_municipio
    )
