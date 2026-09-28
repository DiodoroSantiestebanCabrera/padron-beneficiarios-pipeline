"""Contrato programático de columnas, dominios y constantes de negocio del padrón.

Este módulo es la única fuente de verdad en código Python para:
- Nombres de columnas de entrada (Bronze) y columnas enriquecidas (Silver/Gold).
- Dominios válidos de diagnóstico de calidad (CURP, RFC, estatus).
- Umbrales y reglas de negocio (RN-06, RN-17, RN-27, RN-34, RN-35).
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Final

# ============================================================================
# 1. RUTAS RELATIVAS DEL REPOSITORIO
# ============================================================================
RUTA_CONTRATO_ODCS: Final[Path] = Path("contracts/padron.odcs.yaml")
RUTA_CATALOGO_MUNICIPIOS: Final[Path] = Path("data/catalogs/claves_municipio.csv")
RUTA_CATALOGO_LOCALIDADES: Final[Path] = Path("data/catalogs/claves_localidad.csv")

# ============================================================================
# 2. REGLAS NUMÉRICAS Y EXPRESIONES REGULARES DE NEGOCIO
# ============================================================================
# RN-27: Los folios anteriores a 225001 pertenecen a plásticos legacy y se excluyen del operativo.
FOLIO_MINIMO_VIGENTE: Final[int] = 225001

# Expresión regular oficial para validación sintáctica de CURP (18 caracteres).
REGEX_CURP_OFICIAL: Final[str] = (
    r"^[A-Z]{4}\d{6}[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d$"
)

# Umbral mínimo de similitud para resolución geográfica con rapidfuzz (Fase 3).
UMBRAL_SIMILITUD_GEOGRAFIA: Final[float] = 85.0


# ============================================================================
# 3. NOMBRES DE COLUMNAS DEL PADRÓN (SIN LITERALES DISPERSOS)
# ============================================================================
class ColumnaPadron(StrEnum):
    """Columnas esperadas en los archivos fuente y transformaciones Silver."""

    FOLIO_TARJETA = "FOLIO DE TARJETA"
    CURP = "CURP"
    RFC = "RFC"
    NOMBRE = "NOMBRE"
    PRIMER_APELLIDO = "PRIMER APELLIDO"
    SEGUNDO_APELLIDO = "SEGUNDO APELLIDO"
    FECHA_NACIMIENTO = "F. NAC."
    EDAD = "EDAD"
    GENERO = "GENERO"
    MUNICIPIO = "MUNICIPIO"
    CLAVE_MUNICIPIO_ORIGEN = "CLAVE MUNICIPIO"
    LOCALIDAD = "LOCALIDAD"
    COLONIA = "COLONIA"
    ESTATUS_TARJETA = "ESTATUS"

    # Columnas generadas en Silver (limpieza, geografía y cuarentena)
    DIAGNOSTICO_CURP = "diagnostico_curp"
    DIAGNOSTICO_RFC = "diagnostico_rfc"
    CLAVE_MUNICIPIO_INEGI = "clave_municipio_inegi"
    CLAVE_LOCALIDAD_INEGI = "clave_localidad_inegi"
    SCORE_MATCH_MUNICIPIO = "score_match_municipio"
    SCORE_MATCH_LOCALIDAD = "score_match_localidad"
    MOTIVO_CUARENTENA = "motivo_cuarentena"
    PERIODO = "anio_mes"


# ============================================================================
# 4. DOMINIOS CONTROLADOS DE DIAGNÓSTICO Y RECONCILIACIÓN
# ============================================================================
class DiagnosticoCurp(StrEnum):
    """Valores posibles emitidos por diagnosticar_curp en src/silver/limpieza.py."""

    VALIDA = "VALIDA"
    LONGITUD_MAYOR_A_18 = "LONGITUD_MAYOR_A_18"
    LONGITUD_MENOR_A_18 = "LONGITUD_MENOR_A_18"
    PATRON_INCORRECTO = "PATRON_INCORRECTO"
    CURP_NULA = "CURP_NULA"


class TipoMovimientoPadron(StrEnum):
    """Clasificación de registros resultante de la reconciliación mensual."""

    ALTA = "ALTA"
    BAJA = "BAJA"
    PERMANENCIA = "PERMANENCIA"
    PERMANENCIA_OBSERVADA_CURP = "PERMANENCIA_OBSERVADA_CURP"
    REACTIVACION = "REACTIVACION"


class MotivoExclusionOCuarentena(StrEnum):
    """Causas estandarizadas por las que un registro no entra al operativo limpio."""

    FOLIO_LEGACY_MENOR_225001 = "FOLIO_LEGACY_MENOR_225001"
    FOLIO_NULO_O_INVALIDO = "FOLIO_NULO_O_INVALIDO"
    BAJA_POR_NO_USO = "BAJA_POR_NO_USO"
    CURP_NO_VALIDA_EN_ALTA = "CURP_NO_VALIDA_EN_ALTA"
    GEOGRAFIA_NO_RESUELTA = "GEOGRAFIA_NO_RESUELTA"


COLUMNAS_OBLIGATORIAS_BRONZE: Final[tuple[str, ...]] = (
    ColumnaPadron.FOLIO_TARJETA.value,
    ColumnaPadron.CURP.value,
    ColumnaPadron.MUNICIPIO.value,
)

VALORES_DIAGNOSTICO_CURP_PERMITIDOS: Final[frozenset[str]] = frozenset(
    estado.value for estado in DiagnosticoCurp
)
