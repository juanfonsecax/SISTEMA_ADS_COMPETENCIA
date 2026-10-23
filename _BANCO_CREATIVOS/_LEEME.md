# BANCO DE CREATIVOS DE REFERENCIA

> **Qué es:** las referencias visuales del mercado GT, ordenadas por `concepto_key`.
> Son **referencias para producir**, no creativos para pautar. Nunca se sube una de estas a Meta.
> **Semilla:** las 44 imágenes que el operador organizó a mano (19-ago), cruzadas contra el banco
> y clasificadas con el catálogo. Índice completo en `_INDICE.csv`.

**Dueño de las definiciones: `../\_CATALOGO_CONCEPTOS.md`.** Acá solo viven los archivos.

---

## Cómo está nombrado cada archivo

```
[variante]__[tienda]__[id-original].jpg
```

- **`variante`** — la sub-lectura del operador dentro del concepto (`ligera`, `densa`, `colage-sintomas`, `ugc`, `unboxing`, `antes-despues`, `progresion`, `deseo`, `oferta`, `problema-grande`). Se conserva porque es una segunda opinión independiente y en dos casos corrigió la clasificación automática.
- **`tienda`** — el anunciante, para ver de un vistazo si un concepto viene de uno solo o de varios.
- **`id-original`** — el nombre en `../_IMG/`, para volver al origen y a su fila en `_CLASIF_FAVORITOS.csv`.

## Qué hay hoy

| Concepto | refs | ojo con |
|---|---|---|
| `C2_BENEFICIOS` | 13 | **el concepto de control de FASE 1.** Tres variantes: `ligera` (3), `densa` (8), `colage-sintomas` (1) |
| `C4_TRANSFORMACION` | 7 | 2 de ellas en estética UGC (foto casera), no de estudio |
| `C8_PROGRESION` | 7 | 5 de KetsalStore — transversalidad todavía débil |
| `C5_PRUEBA` | 7 | incluye foto cruda, selfie, bodegón y unboxing |
| `C7_DESEO` | 5 | **las 5 son de Aurora GT.** Un solo anunciante: tratar como hipótesis |
| `C1_OFERTA` | 2 | |
| `C3_SINTOMA` | 2 | |
| `C9_COMPARACION` | 5 | `Yo SIN :( / Yo CON :)`, `FALSA|REAL` y variantes de comparación |

---

## Los dos ejes — no confundirlos

El operador agrupó originalmente un bloque como **"UGC / post orgánico"**. Eso **no es un concepto**: es una **estética**, y esas 8 imágenes cayeron en tres conceptos distintos (C5, C4 y C3).

```
CONCEPTO  = QUÉ muestra   (los 8 valores de concepto_key)
ESTÉTICA  = CÓMO se ve    (cartel publicitario | orgánico-UGC)
```

Son ortogonales: `C8_PROGRESION` existe en cartel (los riñones de KetsalStore) y en orgánico (los rostros dibujados de Doña Oferta). **Si se mezclan en un mismo test, no se puede atribuir el resultado a ninguno de los dos.** Por eso el eje que se registra en `_DIM_CONJUNTOS.csv` es el CONCEPTO; la estética se elige y se deja fija.

---

## Reglas de uso

1. **Referencia, nunca creativo.** Meta detecta el reuso por huella de contenido (`Ads/_TOOLS/LAVADO.md`): subir una de estas es baneo silencioso con el CPM por las nubes.
2. **En FASE 1 se usa una sola:** la variante `ligera` de `C2_BENEFICIOS`, igual en los 6 conjuntos. Prompt en `PLANTILLAS_ADS.md` → PROMPT DE CONTROL FASE 1.
3. **En FASE 2 se abre el abanico:** 6 conceptos, uno por conjunto, con los 15 estilos anti-fatiga rotando.
4. **Al agregar referencias nuevas:** copiarlas acá con el mismo patrón de nombre y agregar su fila a `_INDICE.csv`. Si aparece un dispositivo que no encaja en ninguno de los 8, **no forzarlo** — anotarlo en el catálogo como candidato y esperar a verlo en un segundo anunciante antes de darle `concepto_key` propio.
5. **Un concepto con un solo anunciante es hipótesis, no plantilla.** Hoy aplica a `C7_DESEO` (5 refs, todas de Aurora GT).
