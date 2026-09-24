# ADR-001: Corrección de bugs críticos detectados en la auditoría 2026-09

**Fecha:** 2026-09-24
**Estado:** Aceptado
**Decisores:** Diodoro Santiesteban
**Contexto de la rama:** `feature/hygiene-and-audit-fixes`

## Context

Durante la implementación del componente de exploración visual del pipeline
Silver, se detectó que un intento de instalar `ydata-profiling` fallaba por
`ModuleNotFoundError: No module named 'pkg_resources'`. La investigación
inicial atribuyó el problema a la librería, pero la auditoría posterior
identificó que el código propio contenía 7 bugs independientes que se
manifestarían con datos reales del OLTP.

## Problem

Los siguientes bugs se confirmaron empíricamente con tests que fallaban:

1. **C1** — `limpieza.py` fallaba con `TypeError`/`AttributeError` cuando pandas
   entregaba celdas vacías como `NaN` en lugar de `None`.
2. **C2** — `reconciliacion_padron.py` daba de baja todas las CURPs nulas del
   operativo cuando el lote nuevo traía una CURP nula (porque `Series.isin`
   empareja `NaN` con `NaN`).
3. **H1** — `validar_integridad_folios` no detectaba folios duplicados si uno
   estaba como `int` y el otro como `str`.
4. **H4** — `limpiar_espacios_invisibles` eliminaba tabs en lugar de
   convertirlos en espacios (`"JUAN\tPEREZ"` → `"JUANPEREZ"`).
5. **RN-06** — `curp_consistente_con_fecha_nacimiento` fallaba si `F. NAC.`
   llegaba como `str` (Excel) en lugar de `date`.
6. **M2** — `reconciliar_periodo` usaba `assert` para verificar la
   reconciliación de conteo, que se desactiva con `python -O`.
7. **C3** — `.gitignore` no protegía `data/raw/**`, `data/synthetic/**` ni
   archivos `.xlsx`, lo que exponía PII con un `git add .` accidental.

## Options

### Bug C1
- **(a)** Filtrar `NaN` en la capa de lectura del Excel.
- **(b)** Usar `pd.isna()` en cada función de limpieza. **← Elegida**
- **(c)** Usar `dropna()` antes de la limpieza.

### Bug C2
- **(a)** Excluir CURPs nulas del set de comparación. **← Elegida**
- **(b)** Reemplazar `NaN` por un centinela único por fila.
- **(c)** Usar `pd.NA` en lugar de `np.nan`.

### Bug H1
- **(a)** Normalizar folios con `pd.to_numeric(...).astype("Int64")`. **← Elegida**
- **(b)** Convertir todo a `str` antes de comparar.

## Decision

- **C1:** `pd.isna()` en todas las funciones que reciben valores de pandas.
  Justificación: es la API oficial de pandas para detección de nulos y cubre
  `None`, `NaN`, `pd.NaT` y `pd.NA`.
- **C2:** `.dropna()` sobre las series de CURP antes de construir el set.
  Justificación: una CURP nula no identifica a nadie; nunca debe emparejar.
- **H1:** Normalización a `Int64` (nullable integer) antes de comparar.
  Justificación: los datos reales pueden traer folios como str desde Excel.
- **H4:** Reordenar las operaciones para convertir `\t` a espacio **antes** de
  eliminar caracteres de control.
- **RN-06:** Añadir `_a_fecha()` que normaliza `date`, `datetime` y `str` a
  `datetime.date`.
- **M2:** Reemplazar `assert` por `ReconciliacionError` explícita.
- **C3:** Reforzar `.gitignore` con reglas de proyecto documentadas.

## Consequences

### Positivas
- 23 tests verdes (14 originales + 9 que reproducen los bugs).
- El pipeline puede procesar Excel real con celdas vacías.
- La reconciliación es correcta con CURPs nulas.
- La detección de folios duplicados funciona con tipos mixtos.
- El `.gitignore` protege contra fugas accidentales de PII.

### Negativas / Trade-offs
- El uso de `Int64` en lugar de `int64` cambia el tipo de la columna, lo que
  puede afectar downstream. Documentado y verificado en tests.
- `pd.isna()` es más costoso que `is None`, pero la diferencia es despreciable
  a la escala del proyecto.

## References
- `PROJECT_CONTEXT.md` §13 (Problemas, riesgos y deuda técnica)
- Issue de `ydata-profiling` #1816 (bug de `pkg_resources`, no fusionado)
- Documentación oficial de pandas: `pd.isna`
- PEP 735: grupos de dependencias