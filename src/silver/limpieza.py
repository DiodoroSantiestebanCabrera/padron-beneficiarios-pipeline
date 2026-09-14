"""Limpieza de texto y validación de identidad (CURP/RFC) para la capa Silver.

Corrige errores de codificación (mojibake), elimina caracteres invisibles,
y valida la estructura de CURP/RFC -- sin inventar ni corregir el contenido
de un identificador de identidad, solo detecta si cumple el formato oficial."""

import re
import unicodedata
from datetime import date

import ftfy
import pandas as pd

PATRON_CURP = re.compile(r"^[A-Z]{4}\d{6}[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d$")
LONGITUD_CURP = 18
LONGITUD_RFC_PERSONA_FISICA = 13

COLUMNAS_DE_TEXTO_A_NORMALIZAR = [
    "NOMBRE",
    "APELLIDO PATERNO",
    "APELLIDO MATERNO",
    "MUNICIPIO",
    "COLONIA",
    "CALLE",
]


def corregir_encoding(texto: str | None) -> str | None:
    """Revierte mojibake (ej. 'Jos?' -> 'José') usando ftfy. No inventa
    contenido perdido -- si el carácter original ya no está recuperable,
    ftfy deja el texto tal cual, no adivina."""
    if texto is None:
        return None
    return ftfy.fix_text(texto)


def limpiar_espacios_invisibles(texto: str | None) -> str | None:
    """Elimina espacios 'duros' (\\xa0) y caracteres de control invisibles,
    y colapsa espacios múltiples -- .strip() por sí solo no cubre esto."""
    if texto is None:
        return None
    texto = texto.replace("\xa0", " ")
    texto = "".join(
        caracter for caracter in texto if unicodedata.category(caracter)[0] != "C"
    )
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_texto(texto: str | None) -> str | None:
    """Punto de entrada único para limpiar una columna de texto: primero
    corrige codificación, luego limpia espacios invisibles."""
    return limpiar_espacios_invisibles(corregir_encoding(texto))


def diagnosticar_curp(curp: str | None) -> str:
    """Clasifica un CURP en una categoría específica -- distingue 'más
    largo de lo debido' de 'patrón incorrecto', para que tú decidas qué
    hacer con cada caso por separado."""
    if curp is None:
        return "CURP_NULA"

    curp_limpio = curp.strip().upper()
    longitud = len(curp_limpio)

    if longitud > LONGITUD_CURP:
        return "LONGITUD_MAYOR_A_18"
    if longitud < LONGITUD_CURP:
        return "LONGITUD_MENOR_A_18"
    if not PATRON_CURP.match(curp_limpio):
        return "PATRON_INCORRECTO"
    return "VALIDA"


def diagnosticar_rfc(rfc: str | None) -> str:
    """Clasifica un RFC según su longitud frente al esperado para persona
    física (13 caracteres)."""
    if rfc is None:
        return "RFC_NULO"

    longitud = len(rfc.strip())
    if longitud > LONGITUD_RFC_PERSONA_FISICA:
        return "LONGITUD_MAYOR_A_13"
    if longitud < LONGITUD_RFC_PERSONA_FISICA:
        return "LONGITUD_MENOR_A_13"
    return "VALIDO"


def curp_consistente_con_fecha_nacimiento(
    curp: str | None, fecha_nacimiento: date | None
) -> bool | None:
    """Compara la fecha de nacimiento CODIFICADA dentro del CURP (posiciones
    5 a 10) contra la columna F. NAC. capturada por separado. Devuelve None
    (no comparable) si el CURP es muy corto para extraer esas posiciones,
    o si no hay fecha de nacimiento capturada."""
    if curp is None or fecha_nacimiento is None or len(curp) < 10:
        return None
    fecha_codificada_en_curp = curp[4:10]
    fecha_esperada = fecha_nacimiento.strftime("%y%m%d")
    return fecha_codificada_en_curp == fecha_esperada


def limpiar_padron(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza texto y diagnostica calidad de CURP/RFC en columnas
    propias -- ninguna fila se excluye aquí."""
    df_normalizado = df.copy()

    for columna in COLUMNAS_DE_TEXTO_A_NORMALIZAR:
        if columna in df_normalizado.columns:
            df_normalizado[columna] = df_normalizado[columna].apply(normalizar_texto)

    df_normalizado["diagnostico_curp"] = df_normalizado["CURP"].apply(diagnosticar_curp)
    df_normalizado["diagnostico_rfc"] = df_normalizado["RFC"].apply(diagnosticar_rfc)

    if "F. NAC." in df_normalizado.columns:
        df_normalizado["curp_consistente_con_fecha"] = df_normalizado.apply(
            lambda fila: curp_consistente_con_fecha_nacimiento(
                fila["CURP"], fila["F. NAC."]
            ),
            axis=1,
        )

    return df_normalizado
