"""Reconciliación periódica del padrón: incorpora un nuevo PadronVigente
al PadronMaestroOperativo acumulado, detectando duplicidad de folio (alerta
de integridad) y de CURP (actualización esperada -- el folio más reciente
reemplaza al anterior)."""

from dataclasses import dataclass

import pandas as pd


class IntegridadFolioError(Exception):
    """Se lanza cuando un folio aparece duplicado de forma inesperada --
    nunca debe pasar en un periodo legítimo, así que no se procesa como
    una baja de negocio normal, se detiene el pipeline para revisión."""


@dataclass
class ResultadoReconciliacion:
    """Agrupa los dos resultados de reconciliar un periodo: la tabla
    operativa actualizada, y el detalle de qué se dio de baja y por qué."""

    padron_maestro_operativo_nuevo: pd.DataFrame
    snapshot_bajas: pd.DataFrame


def _normalizar_curp(serie_curp: pd.Series) -> pd.Series:
    """Uniforma mayúsculas y espacios antes de comparar."""
    return serie_curp.str.strip().str.upper()


def validar_integridad_folios(
    operativo_actual: pd.DataFrame, vigente_nuevo: pd.DataFrame
) -> None:
    """Verifica que ningún folio se repita donde no debería."""
    folios_duplicados_en_vigente = vigente_nuevo["FOLIO DE TARJETA"].duplicated()
    if folios_duplicados_en_vigente.any():
        raise IntegridadFolioError(
            f"El periodo nuevo trae {folios_duplicados_en_vigente.sum()} folios "
            "repetidos dentro de sí mismo."
        )

    folios_ya_existentes = vigente_nuevo["FOLIO DE TARJETA"].isin(
        operativo_actual["FOLIO DE TARJETA"]
    )
    if folios_ya_existentes.any():
        raise IntegridadFolioError(
            f"{folios_ya_existentes.sum()} folio(s) del periodo nuevo ya existen "
            "en PadronMaestroOperativo -- posible error de captura del OLTP."
        )


def identificar_bajas_por_curp_duplicada(
    operativo_actual: pd.DataFrame, vigente_nuevo: pd.DataFrame
) -> pd.DataFrame:
    """Encuentra folios del padrón operativo actual cuya CURP también
    aparece en el periodo nuevo -- son la versión vieja de una actualización."""
    curps_del_periodo_nuevo = set(_normalizar_curp(vigente_nuevo["CURP"]))
    mascara_reemplazados = _normalizar_curp(operativo_actual["CURP"]).isin(
        curps_del_periodo_nuevo
    )

    bajas = operativo_actual.loc[
        mascara_reemplazados, ["FOLIO DE TARJETA", "CURP"]
    ].copy()
    bajas["motivo_baja"] = "CURP_DUPLICADA_CON_PERIODO_NUEVO"
    return bajas


def reconciliar_periodo(
    padron_maestro_operativo_actual: pd.DataFrame,
    padron_vigente_nuevo: pd.DataFrame,
    periodo: str,
) -> ResultadoReconciliacion:
    """Incorpora un periodo nuevo al PadronMaestroOperativo acumulado."""
    validar_integridad_folios(padron_maestro_operativo_actual, padron_vigente_nuevo)

    bajas = identificar_bajas_por_curp_duplicada(
        padron_maestro_operativo_actual, padron_vigente_nuevo
    )
    bajas["periodo"] = periodo

    folios_a_descartar = set(bajas["FOLIO DE TARJETA"])
    operativo_sin_reemplazados = padron_maestro_operativo_actual[
        ~padron_maestro_operativo_actual["FOLIO DE TARJETA"].isin(folios_a_descartar)
    ]

    operativo_nuevo = pd.concat(
        [operativo_sin_reemplazados, padron_vigente_nuevo], ignore_index=True
    )

    conteo_esperado = (
        len(padron_maestro_operativo_actual) - len(bajas) + len(padron_vigente_nuevo)
    )
    assert len(operativo_nuevo) == conteo_esperado, (
        f"Reconciliación inconsistente: se esperaban {conteo_esperado} filas, "
        f"resultaron {len(operativo_nuevo)}"
    )

    return ResultadoReconciliacion(
        padron_maestro_operativo_nuevo=operativo_nuevo,
        snapshot_bajas=bajas,
    )
