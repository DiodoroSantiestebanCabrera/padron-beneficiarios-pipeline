# tests/test_generar_datos_sinteticos.py
"""Pruebas para src/utils/generar_datos_sinteticos.py"""

from src.utils.generar_datos_sinteticos import generar_padron_sintetico


def test_genera_el_numero_de_filas_solicitado():
    df = generar_padron_sintetico(n_filas=100)
    assert len(df) == 100


def test_tiene_las_29_columnas_reales():
    df = generar_padron_sintetico(n_filas=10)
    assert len(df.columns) == 29


def test_parentesco_siempre_es_titular():
    df = generar_padron_sintetico(n_filas=500)
    assert set(df["PARENTESCO"].unique()) == {"Titular"}
