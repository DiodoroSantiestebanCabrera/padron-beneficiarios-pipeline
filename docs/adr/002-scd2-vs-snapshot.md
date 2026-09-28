# ADR-002: Modelado Histórico con SCD Tipo 2 en DimBeneficiario y Snapshot Mensual en Hechos (RN-34)

* **Estado:** Aceptado
* **Fecha:** 2026-09-28
* **Contexto:** Fase 2 — Resolución de bloqueador RN-34 para diseño de persistencia y capa Gold.

## 1. Contexto y Problema
El padrón de beneficiarios se procesa en cortes mensuales (`anio_mes`). Durante la vida del programa social, los atributos descriptivos o geográficos de un beneficiario (como domicilio, localidad o municipio) pueden cambiar entre periodos, además de su estatus de vigencia (alta, permanencia, baja). Se requiere decidir entre:
1. Sobrescribir atributos manteniendo solo un snapshot mensual de bajas.
2. Implementar **Slowly Changing Dimension Tipo 2 (SCD2)** en `DimBeneficiario` combinado con tablas de hechos bien delimitadas en su granularidad.

## 2. Decisión
Adoptar **SCD Tipo 2** en `DimBeneficiario` utilizando una **clave subrogada (`beneficiario_sk`)** y separar la representación de hechos en el esquema estrella de la capa Gold:

1. **`DimBeneficiario` (SCD Tipo 2):**
   * `beneficiario_sk` (PK subrogada única por versión del registro).
   * `curp` (llave natural cuando `diagnostico_curp == 'VALIDA'`).
   * `folio_tarjeta_actual` (`Int64`).
   * Atributos descriptivos: nombre completo normalizado, `rfc`, `fecha_nacimiento`, `genero`.
   * Columnas de control SCD2: `fecha_inicio_vigencia` (`YYYY-MM-DD`), `fecha_fin_vigencia` (`YYYY-MM-DD` o `NULL`), `es_actual` (`bool`).
2. **`FactPadronMensual` (Periodic Snapshot Fact Table):**
   * Granularidad estricta: **1 fila por tarjeta/beneficiario activo por `anio_mes`**.
   * Llaves foráneas hacia claves subrogadas: `beneficiario_sk`, `municipio_id`, `localidad_id`, `tiempo_id`.
3. **`FactMovimientosPadron` (Transaction Fact Table):**
   * Granularidad: **1 fila por evento de reconciliación mensual** (`ALTA`, `BAJA`, `PERMANENCIA`, `REACTIVACION`) ocurrido en el periodo `anio_mes`.

## 3. Justificación Técnica
* Si `DimBeneficiario` implementa SCD Tipo 2, una misma `CURP` tendrá múltiples filas históricas a lo largo del tiempo. Usar `CURP` directamente como llave foránea en la tabla de hechos rompería la integridad 1:N en SQL Server (`MasterDB`), Power BI y Databricks Unity Catalog, multiplicando filas en los `JOIN`. La clave subrogada `beneficiario_sk` preserva la cardinalidad exacta del esquema estrella.
* En Databricks (Fase 7), este patrón se implementa transaccionalmente mediante `DeltaTable.merge()` (`MERGE INTO`).

## 4. Consecuencias
* **Positivas:** Trazabilidad histórica completa para auditorías gubernamentales; consultas de BI sin ambigüedad de cardinalidad; demostración verificable de modelado dimensional en portafolio.
* **Negativas / Costo:** La generación de `DimBeneficiario` requiere calcular un hash de atributos mudables (`row_hash`) para detectar cambios reales entre el periodo `t-1` y el periodo `t`.