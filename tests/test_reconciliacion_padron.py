"""Pruebas de reconciliación usando el generador de datos sintéticos."""

import pytest

from src.silver.reconciliacion_padron import (
    IntegridadFolioError,
    reconciliar_periodo,
    validar_integridad_folios,
)
from src.utils.generar_datos_sinteticos import (
    generar_padron_sintetico,
    generar_periodo_siguiente,
)


def test_reconciliacion_detecta_y_reemplaza_curps_duplicadas():
    padron_marzo = generar_padron_sintetico(n_filas=1000, anio_mes="2026-03")
    padron_abril = generar_periodo_siguiente(
        padron_marzo,
        n_filas_nuevas=200,
        anio_mes="2026-04",
        proporcion_curps_repetidas=0.1,
    )

    resultado = reconciliar_periodo(padron_marzo, padron_abril, periodo="2026-04")

    assert len(resultado.snapshot_bajas) == 20  # 10% de 200
    assert len(resultado.padron_maestro_operativo_nuevo) == 1000 - 20 + 200


def test_folio_duplicado_lanza_error():
    padron = generar_padron_sintetico(n_filas=100, anio_mes="2026-03")
    periodo_con_folio_repetido = padron.iloc[
        [0]
    ]  # copia una fila que ya existe, folio incluido

    with pytest.raises(IntegridadFolioError):
        validar_integridad_folios(padron, periodo_con_folio_repetido)
