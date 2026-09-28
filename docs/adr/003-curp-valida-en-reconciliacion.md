# ADR-003: Reconciliación Jerárquica de Identidad por CURP Válida y Respaldo por Folio de Tarjeta (RN-35)

* **Estado:** Aceptado
* **Fecha:** 2026-09-28
* **Contexto:** Fase 2 — Resolución de bloqueador RN-35 sobre reglas de cruce en `src/silver/reconciliacion_padron.py`.

## 1. Contexto y Problema
El módulo `src/silver/limpieza.py` aplica la regla de anotar y no excluir, asignando en la columna `diagnostico_curp` uno de cinco estados: `VALIDA`, `LONGITUD_MAYOR_A_18`, `LONGITUD_MENOR_A_18`, `PATRON_INCORRECTO` o `CURP_NULA`.
Al reconciliar el padrón operativo (`t-1`) contra el nuevo corte mensual (`t`), existen dos riesgos opuestos:
1. **Riesgo de colisión de identidad:** Si se cruzan cadenas de `CURP` inválidas (por ejemplo, textos genéricos como `"SIN CURP"` o `"XXXX000000XXXXXX00"`), personas distintas se fusionarán como si fueran el mismo beneficiario.
2. **Riesgo de baja falsa:** Si un beneficiario activo en `t-1` tiene su `CURP` en estado inválido o nulo pero cuenta con un `FOLIO DE TARJETA` válido (`>= 225001`), y en el mes `t` sigue apareciendo con el mismo `FOLIO DE TARJETA`, ignorarlo por completo en el cruce haría que el sistema lo clasifique como ausente en `t` y ejecute una **baja automática improcedente**.

## 2. Decisión
Implementar una **resolución de identidad determinista en dos etapas** durante la reconciliación mensual:

1. **Etapa 1 — Cruce primario por `CURP` verificada:**
   * Solo participan en el cruce por `CURP` los registros donde `diagnostico_curp == "VALIDA"` tanto en el operativo como en el nuevo corte.
2. **Etapa 2 — Cruce secundario de protección por `FOLIO DE TARJETA`:**
   * Para los registros que no pudieron emparejarse en la Etapa 1 debido a que su `diagnostico_curp != "VALIDA"`, el emparejamiento contra el padrón operativo se realiza mediante `FOLIO DE TARJETA` (normalizado a `Int64` y `>= 225001`).
   * Si el `FOLIO DE TARJETA` coincide, el beneficiario conserva su continuidad (`PERMANENCIA_CON_OBSERVACION_CURP`) y se emite la alerta correspondiente hacia la tabla/reporte de cuarentena para subsanación administrativa, evitando su baja equivocada.
   * Los registros de nuevo ingreso (`ALTA` candidata) que presenten `diagnostico_curp != "VALIDA"` no ingresan al padrón operativo limpio hasta subsanar su identidad: se desvían a la tabla de **Cuarentena** con motivo explícito.

## 3. Consecuencias
* **Positivas:** Cero fusiones erróneas entre personas distintas con CURPs mal capturadas y cero bajas falsas de beneficiarios activos identificables por su número de tarjeta.
* **Verificación:** Codificado en el contrato `src/contrato.py` y exigido mediante pruebas unitarias en `tests/test_reconciliacion.py`.