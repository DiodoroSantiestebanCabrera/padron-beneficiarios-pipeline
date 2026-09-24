"""Tests que reproducen los bugs documentados en PROJECT_CONTEXT.md.

Estos tests DEBEN FALLAR antes de aplicar los fixes.
Despues de aplicar los fixes, deben PASAR.
"""

import numpy as np
import pandas as pd
import pytest

from src.silver.limpieza import (
    curp_consistente_con_fecha_nacimiento,
    diagnosticar_curp,
    diagnosticar_rfc,
    limpiar_espacios_invisibles,
    normalizar_texto,
)
from src.silver.reconciliacion_padron import (
    IntegridadFolioError,
    reconciliar_periodo,
    validar_integridad_folios,
)

# ============================================================
# BUG C1 - NaN de pandas rompe la limpieza
# ============================================================


class TestBugC1NaN:
    """Pandas convierte celdas vacias en NaN, no en None."""

    def test_normalizar_texto_con_nan_no_falla(self):
        assert normalizar_texto(np.nan) is None

    def test_diagnosticar_curp_con_nan(self):
        assert diagnosticar_curp(np.nan) == "CURP_NULA"

    def test_diagnosticar_rfc_con_nan(self):
        assert diagnosticar_rfc(np.nan) == "RFC_NULO"

    def test_limpiar_espacios_con_nan_no_falla(self):
        assert limpiar_espacios_invisibles(np.nan) is None


# ============================================================
# BUG C2 - CURP nula empareja con CURP nula
# ============================================================


class TestBugC2CurpNula:
    """Una CURP nula NO identifica a nadie."""

    def test_curp_nula_no_produce_bajas_masivas(self):
        operativo = pd.DataFrame(
            {
                "FOLIO DE TARJETA": [1, 2, 3],
                "CURP": [None, None, "ABCD801231HDFXXX01"],
            }
        )
        vigente = pd.DataFrame(
            {
                "FOLIO DE TARJETA": [4],
                "CURP": [None],
            }
        )
        resultado = reconciliar_periodo(operativo, vigente, "2026-08")
        assert len(resultado.snapshot_bajas) == 0


# ============================================================
# BUG H1 - Folio int vs str
# ============================================================


class TestBugH1FolioTipo:
    """Si operativo tiene int y nuevo tiene str, debe detectarse."""

    def test_folio_int_vs_str_se_detecta(self):
        operativo = pd.DataFrame(
            {
                "FOLIO DE TARJETA": [225001],
                "CURP": ["X"],
            }
        )
        vigente = pd.DataFrame(
            {
                "FOLIO DE TARJETA": ["225001"],
                "CURP": ["Y"],
            }
        )
        with pytest.raises(IntegridadFolioError):
            validar_integridad_folios(operativo, vigente)


# ============================================================
# BUG H4 - Tab se elimina en lugar de convertirse en espacio
# ============================================================


class TestBugH4Tab:
    """Un tab entre palabras debe convertirse en espacio."""

    def test_tab_se_convierte_en_espacio(self):
        assert limpiar_espacios_invisibles("JUAN\tPEREZ") == "JUAN PEREZ"

    def test_multiples_tabs_colapsan(self):
        assert limpiar_espacios_invisibles("A\t\tB\tC") == "A B C"


# ============================================================
# BUG RN-06 - F. NAC. llega como str desde Excel/CSV
# ============================================================


class TestBugRN06FechaStr:
    """La funcion debe aceptar tanto date como str."""

    def test_fecha_como_str_no_falla(self):
        resultado = curp_consistente_con_fecha_nacimiento(
            "ABCD801231HDFXXX01", "1980-12-31"
        )
        assert resultado is True
