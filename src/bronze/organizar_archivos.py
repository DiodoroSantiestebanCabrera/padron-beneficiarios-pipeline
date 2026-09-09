"""Organiza los reportes mensuales del padrón en carpetas por periodo."""

import re
import shutil
from pathlib import Path

MESES_ES = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}

CARPETA_ENTRANTE = Path("data/raw/incoming")
CARPETA_RAW = Path("data/raw")


def extraer_periodo(nombre_archivo: str) -> str:
    """Obtiene el periodo de cierre ('YYYY-MM') a partir del nombre del reporte.

    Tolera que el nombre use espacios o guiones bajos como separador.
    """
    palabras = re.split(r"[\s_]+", nombre_archivo.upper())

    meses_encontrados = [palabra for palabra in palabras if palabra in MESES_ES]
    if not meses_encontrados:
        raise ValueError(f"No se encontró un mes válido en: {nombre_archivo}")

    anios_encontrados = [
        palabra for palabra in palabras if palabra.isdigit() and len(palabra) == 4
    ]
    if not anios_encontrados:
        raise ValueError(f"No se encontró un año en: {nombre_archivo}")

    mes_cierre = meses_encontrados[-1]
    anio_cierre = anios_encontrados[-1]

    return f"{anio_cierre}-{MESES_ES[mes_cierre]:02d}"


def organizar_archivos_entrantes() -> None:
    """Mueve cada Excel nuevo de data/raw/incoming/ a su carpeta data/raw/YYYY-MM/."""
    if not CARPETA_ENTRANTE.exists():
        raise FileNotFoundError(f"No existe la carpeta de entrada: {CARPETA_ENTRANTE}")

    archivos_nuevos = list(CARPETA_ENTRANTE.glob("*.xlsx"))
    archivos_rechazados = []

    for archivo in archivos_nuevos:
        try:
            periodo = extraer_periodo(archivo.name)
        except ValueError as error:
            archivos_rechazados.append((archivo.name, str(error)))
            continue

        carpeta_destino = CARPETA_RAW / periodo
        ##exist_ok --> si la carpeta que quiero crear(mkdir carpeta_destino) YA EXISTE, no truena
        ##parents -->parents si a ese carpeta le faltan carpetas arriba para crearse, las crea tambien
        carpeta_destino.mkdir(parents=True, exist_ok=True)
        # shutil siempre recibe string, recibe documento y lo mueve a la carpeta destino
        shutil.move(str(archivo), str(carpeta_destino / archivo.name))
        print(f"{archivo.name} -> {carpeta_destino}/")

    if archivos_rechazados:
        print(f"\n{len(archivos_rechazados)} archivo(s) no se pudieron organizar:")
        for nombre, motivo in archivos_rechazados:
            print(f"  - {nombre}: {motivo}")
