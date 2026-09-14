"""Pruebas para src/silver/limpieza.py"""

from datetime import date

import pandas as pd

from src.silver.limpieza import (
    curp_consistente_con_fecha_nacimiento,
    diagnosticar_curp,
    diagnosticar_rfc,
    limpiar_espacios_invisibles,
    limpiar_padron,
    normalizar_texto,
)


def test_normalizar_texto_corrige_mojibake():
    assert normalizar_texto("Jos\u00c3\u00a9") == "José"


def test_limpiar_espacios_invisibles_quita_espacio_duro():
    assert limpiar_espacios_invisibles("Tlaxcala\xa0") == "Tlaxcala"


def test_diagnosticar_curp_valida():
    assert diagnosticar_curp("RIPM010517HTLVRRA5") == "VALIDA"


def test_diagnosticar_curp_mas_larga_de_18():
    assert diagnosticar_curp("RIPM010517HTLVRRA5XX") == "LONGITUD_MAYOR_A_18"


def test_diagnosticar_curp_patron_incorrecto_con_longitud_correcta():
    assert diagnosticar_curp("1234567890123456789"[:18]) == "PATRON_INCORRECTO"


def test_diagnosticar_rfc_mas_largo_de_13():
    assert diagnosticar_rfc("RIPM010517AB1XX") == "LONGITUD_MAYOR_A_13"


def test_curp_consistente_con_fecha_nacimiento_coincide():
    assert (
        curp_consistente_con_fecha_nacimiento("RIPM010517HTLVRRA5", date(2001, 5, 17))
        is True
    )


def test_curp_consistente_con_fecha_nacimiento_no_coincide():
    assert (
        curp_consistente_con_fecha_nacimiento("RIPM010517HTLVRRA5", date(2005, 1, 1))
        is False
    )


def test_limpiar_padron_no_excluye_ninguna_fila():
    df = pd.DataFrame(
        {
            "NOMBRE": ["Ana", "Luis"],
            "CURP": ["RIPM010517HTLVRRA5", "CORTO"],
            "RFC": ["RIPM010517AB1", "RIPM010517AB1"],
            "F. NAC.": [date(2001, 5, 17), date(1990, 1, 1)],
        }
    )
    resultado = limpiar_padron(df)
    assert len(resultado) == 2
    assert resultado.iloc[0]["diagnostico_curp"] == "VALIDA"
    assert resultado.iloc[1]["diagnostico_curp"] == "LONGITUD_MENOR_A_18"
