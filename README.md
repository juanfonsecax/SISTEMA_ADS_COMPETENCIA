# SISTEMA ADS COMPETENCIA

Sistema local para conservar, normalizar y revisar anuncios de competencia de Meta Ad Library (Guatemala). La fuente de verdad es una base SQLite canónica; los datos crudos, imágenes y documentos de investigación se conservan como evidencia.

El producto activo es la aplicación `ads_intel`. Los antiguos scripts de descarga, galerías HTML y documentos operativos fueron retirados; su contenido quedó respaldado en los ZIP de recuperación descritos abajo.

## Requisitos

- Python 3.11 o superior.
- Dependencia de miniaturas y firmas visuales:

```text
python -m pip install -r requirements.txt
```

## Punto de entrada

Todos los comandos de la aplicación se ejecutan con un único punto de entrada:

```text
python -m ads_intel.cli --help
```

La base por defecto es `data/ads_intel.db`. Las migraciones se aplican automáticamente al abrir la base. Antes de migrar o reprocesar datos reales, cree un respaldo recuperable.

## Flujo de trabajo

```text
python -m ads_intel.cli freeze
python -m ads_intel.cli import
python -m ads_intel.cli reconcile
python -m ads_intel.cli review-seed
python -m ads_intel.cli review-list --status pending
python -m ads_intel.cli visual-scan --threshold 8
python -m ads_intel.cli visual-list --limit 50
```

- `freeze`: genera el manifiesto de archivos y un respaldo verificable.
- `import`: importa los CSV y documentos canónicos a SQLite de forma idempotente.
- `reconcile`: compara los conteos de la base con los archivos de origen.
- `review-seed`: crea la cola de revisión humana.
- `visual-scan`: calcula firmas dHash, miniaturas y pares candidatos para una ejecución nueva.
- `all`: ejecuta `freeze` e `import` en secuencia.

## Derechos, revisión y exportación

Los derechos de fuente, activo y claim empiezan como desconocidos o pendientes. Ningún valor se aprueba automáticamente.

```text
python -m ads_intel.cli review-record --object asset --object-id 1 --status unknown
python -m ads_intel.cli review-decide --item-id 1 --status resolved --decision "..." --reviewer "..."
python -m ads_intel.cli export-check --object asset --object-id 1
```

`export-check` falla si el objeto no tiene evidencia aprobada, revisor y fecha. Los estados `unknown` y `evidence_needed` son válidos y quedan registrados; no equivalen a una aprobación.

## Similitud visual

La firma usa `dhash` versión `1` (64 bits, distancia Hamming). Un par con distancia menor o igual al umbral es solo un candidato pendiente: no se borra, fusiona ni declara duplicado. Cada ejecución de `visual-scan` queda identificada por su `scan_run_id`; la vista vigente muestra únicamente los candidatos del último escaneo con el umbral solicitado.

```text
python -m ads_intel.cli visual-runs
python -m ads_intel.cli visual-list --run-id 2 --threshold 8
```

El umbral inicial es 8 y no está calibrado contra una verdad humana. Las miniaturas viven en `data/visual_thumbnails/`, fuera de Git.

## Respaldo y restauración

`backup` crea tres inventarios (código activo, datos operativos y recuperación completa), un snapshot consistente de SQLite y un ZIP, y verifica hashes, integridad y claves foráneas.

```text
python -m ads_intel.cli backup
python -m ads_intel.cli restore data/backups/phase2_recovery_<fecha>.zip data/restored
```

Los respaldos y manifiestos se escriben en `data/backups/` y `data/manifests/`. Los ZIP incluyen el código, los datos y una copia de los archivos heredados retirados.

## Estructura

| Ruta | Contenido |
|---|---|
| `ads_intel/` | Aplicación, migraciones y lógica de importación, revisión, similitud e inventarios. |
| `tests/` | Pruebas funcionales con bases temporales. |
| `scripts/full_snapshot.py` | Envoltorio de automatización para `ads_intel.cli backup`. |
| `_ADS.csv`, `_BANCO.csv`, `_COPIES.csv`, `_ETIQUETAS_MANUALES.csv` | Metadatos canónicos de anuncios, copias y etiquetas. |
| `_PAGINAS.csv`, `_RANKING_CUENTAS.csv`, `_SELECCION_EXTRACCION.csv` | Directorio de páginas, ranking y selección. |
| `_CATALOGO_CONCEPTOS.md` | Catálogo de conceptos que consume el importador. |
| `_IMG/` | Imágenes de anuncios, conservadas como evidencia. |
| `_BANCO_CREATIVOS/` | Creativos de referencia y su índice. |
| `_BLUEPRINTS/` | Fichas y esquemas de análisis. |
| `_RAW/` | Exportaciones crudas de Meta Ad Library. |
| `ANALISIS/` | Investigación, metodología y documentos de evidencia. |
| `data/` | Base SQLite, manifiestos, respaldos y miniaturas; ignorada por Git. |

## Pruebas

```text
python -m unittest discover -s tests -v
```

## Límites conocidos

- Los 597 activos permanecen con derechos `unknown` y la fuente con permiso `pending_review` hasta revisión humana.
- Existen 22 elementos de revisión pendientes; no se aprueban por defecto.
- Los pares visuales son candidatos, no identidades ni duplicados confirmados.
- El umbral de similitud requiere calibración con decisiones humanas antes de usarse como criterio de deduplicación.
