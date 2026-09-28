# ADR-004: Alineación de Versión de Python con Databricks Runtime 17.3 LTS (DEC-007)

* **Estado:** Aceptado
* **Fecha:** 2026-09-28
* **Contexto:** Fase 2 — Decisión sobre versión de Python en entorno local, CI y Databricks.

## 1. Contexto
El archivo `.python-version` inicial fijaba Python `3.11.15`. Sin embargo, la Fase 7 del proyecto tiene como destino **Databricks Runtime 17.3 LTS**, cuyo entorno nativo ejecuta **Python 3.12** y **Apache Spark 4.0.0**.

## 2. Decisión
Establecer compatibilidad con `>=3.11,<3.13` en `pyproject.toml` y fijar `.python-version` en `3.12` (o mantener `3.11.15` únicamente si la imagen base del Dev Container actual tiene preinstalado un solo binario de Python 3.11, actualizando el `Dockerfile` a `3.12` antes de iniciar la Fase 7). Todo el código nuevo debe utilizar sintaxis estándar compatible con Python 3.11 y 3.12 (`enum.StrEnum`, `typing.Self`, anotaciones `X | Y`).