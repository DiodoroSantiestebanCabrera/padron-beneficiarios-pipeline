"""Pruebas unitarias y de coherencia entre src/contrato.py y contracts/padron.odcs.yaml."""

from __future__ import annotations

import yaml

from src.contrato import (
    FOLIO_MINIMO_VIGENTE,
    RUTA_CONTRATO_ODCS,
    VALORES_DIAGNOSTICO_CURP_PERMITIDOS,
    ColumnaPadron,
    DiagnosticoCurp,
)


def test_archivo_contrato_odcs_existe_y_es_v3() -> None:
    """Verifica que el archivo YAML del contrato exista y use el esquema ODCS v3.x."""
    assert RUTA_CONTRATO_ODCS.is_file(), (
        f"No se encontró el contrato en {RUTA_CONTRATO_ODCS}"
    )

    contenido = yaml.safe_load(RUTA_CONTRATO_ODCS.read_text(encoding="utf-8"))
    assert contenido["apiVersion"].startswith("v3."), "El contrato debe usar ODCS v3.x"
    assert contenido["kind"] == "DataContract"
    assert "schema" in contenido and isinstance(contenido["schema"], list)


def test_sincronia_folio_minimo_entre_yaml_y_python() -> None:
    """Comprueba que el corte de folio 225001 (RN-27) coincida en el YAML y en Python."""
    contenido = yaml.safe_load(RUTA_CONTRATO_ODCS.read_text(encoding="utf-8"))
    propiedades = contenido["schema"][0]["properties"]

    prop_folio = next(
        p for p in propiedades if p["name"] == ColumnaPadron.FOLIO_TARJETA.value
    )
    minimo_yaml = prop_folio["logicalTypeOptions"]["minimum"]

    assert minimo_yaml == FOLIO_MINIMO_VIGENTE == 225001


def test_dominio_diagnostico_curp_completo() -> None:
    """Verifica que los 5 estados documentados de diagnóstico de CURP estén presentes."""
    esperados = {
        "VALIDA",
        "LONGITUD_MAYOR_A_18",
        "LONGITUD_MENOR_A_18",
        "PATRON_INCORRECTO",
        "CURP_NULA",
    }
    assert VALORES_DIAGNOSTICO_CURP_PERMITIDOS == esperados
    assert DiagnosticoCurp.VALIDA.value in VALORES_DIAGNOSTICO_CURP_PERMITIDOS
