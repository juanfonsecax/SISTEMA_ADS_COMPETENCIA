# SISTEMA INDEPENDIENTE — ANÁLISIS Y BANCO DE ANUNCIOS DE COMPETENCIA (GT)

Módulo autónomo para cosecha, filtrado algorítmico, clasificación y análisis de creativos ganadores de Meta Ad Library (mercado Guatemala / Bienestar).

---

## 1. Visualizadores listos para usar (Doble clic)

- **`_WINNERS.html`**: Visualizador de los **111 creativos favoritos** ya clasificados por concepto (Beneficios, Transformación, Prueba, etc.). Requiere estar en esta carpeta para leer las imágenes de `_IMG/`.
- **`_WINNERS_PORTABLE.html`**: Versión 100% portable con imágenes embebidas en Base64 (ideal para compartir o mover de máquina sin perder referencias).
- **`_GALERIA.html`**: Galería completa de la cosecha (más de 400 anuncios) con filtros por anunciante, ranking, días activos y cuadrantes.

---

## 2. Estructura de carpetas y datos

| Carpeta / Archivo | Contenido |
|---|---|
| `_IMG/` | Imágenes descargadas de competidores organizadas por anunciante. |
| `_RAW/` | Batches crudos extraídos de Meta Ad Library en formato masivo. |
| `_BLUEPRINTS/` | Estructuras visuales maestras y 22 blueprints canónicos validados. |
| `_BANCO_CREATIVOS/` | Banco de creativos segmentado por concepto (`C1_OFERTA` a `C9_COMPARACION`). |
| `ANALISIS/` | Documentos maestros de evidencia, taxonomía y metodología: <br>• `CATALOGO_CONCEPTOS_EVIDENCIA.md`<br>• `INVESTIGACION_MERCADO_FASE01_BASES_VS_SISTEMA.md`<br>• `MATRIZ_METODOLOGIA.md`<br>• `PLANTILLAS_ADS.md` y secciones. |
| `_BANCO.csv`, `_ADS.csv` | Índices de metadatos, réplicas, días y posición por impresiones. |
| `_CLASIF_FAVORITOS.csv` | Clasificación final de los creativos ganadores. |
| `_PAGINAS.csv` | Directorio de páginas competidoras monitoreadas. |

---

## 3. Pipeline de Extracción y Actualización

1. **Extracción en Meta Ad Library**:
   - Abrir Meta Ad Library en un navegador con sesión activa.
   - Inyectar el script [`_EXTRACTOR.js`](_EXTRACTOR.js) en la consola o herramienta de navegador.
   - Extraer la estructura del JSON interno (`search_results_connection`).
2. **Descarga y Deduplicación**:
   - Guardar el bloque en `_RAW/masivo/`.
   - Ejecutar `python bajar2.py` (descarga imágenes deduplicando por hash MD5).
3. **Regeneración de Galerías**:
   - Ejecutar `python gen_galeria.py` para recalcular el score de supervivencia:
     $$\text{Score} = \text{escalado} \times 20 + (15 \text{ si días} \ge 21) + \text{velocidad}$$
   - Ejecutar `python gen_winners.py` para refrescar `_WINNERS.html`.
