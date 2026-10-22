# INVESTIGACIÓN DE MERCADO EN FASE 0/1 — LAS BASES DE TODAS LAS CLASES vs EL SISTEMA

> **Qué es este archivo.** El inventario completo de las **bases y variables de investigación de
> mercado** que exigen todas las fuentes del programa (curso base 1-22, SKOOL, bloque de abril 2026,
> clases nuevas LB, clases Calet, Excel y PDFs), la **extracción profunda de la Clase 22** (los
> 10 aspectos, la estructura del flujo, las fricciones y el umbral cognitivo), y el **diagnóstico
> 1-a-1 contra lo que el SISTEMA VITALCOM ya implementa en FASE 0/1** (de buscar producto a los
> 6 ángulos).
>
> **Qué NO es.** No es un plan de implementación y no cambia ninguna regla. Es lectura y
> diagnóstico: qué dicen las clases, qué hace el sistema hoy, y qué falta o queda parcial.
>
> Última actualización: **2026-10-18** · Corpus analizado: **9 bloques de fuentes** · Sin
> modificaciones al sistema (solo lectura).

---

## 0 · LEYENDA DE FUENTES, MÉTODO Y MAPA DEL PIPELINE

### 0.1 Fuentes indexadas (extiende la leyenda de `MATRIZ_METODOLOGIA.md`)

| ID | Fuente | Autores | Ubicación |
|---|---|---|---|
| **F0** | Currículo SKOOL (módulos 1-6) + clases en vivo SKOOL (6ta, 7ma, 8va) | Mercy Pardo | `AUDIOS CLASES/CLASES SKOOL/` |
| **F1** | Curso base — Clases 1 a 22 | Mercy · Joaquín · Camilo · Pipe | `VITALCOM_CLASES/Clase N - …txt` |
| **F2** | Herramienta de Validación de Productos (Excel) | Mercy Pardo | `VITALCOM_CLASES/Herramienta - Validacion …txt` |
| **F3** | PDFs: Creativos que Venden + Análisis de la Competencia | Joaquín | `VITALCOM_CLASES/PDF …txt` |
| **F4** | Clase 2026-08-16 — Banco de Conceptos 500 Marcas + 1-1-5 | Calet | `VITALCOM_CLASES/Clase 2026-08-16 …txt` |
| **F5** | Clase 2026-08-22 — Escalado 1-1-7, CBO Ventas, Surfing | Calet | `VITALCOM_CLASES/Clase 2026-08-22 …txt` |
| **F6** | DATA PROPIA | — | `_APRENDIZAJES.csv` · auditorías · CSVs |
| **F7** | **Bloque abril 2026** (10 clases procesadas + brutas) | Joaquín et al. | `METODOLOGIA FINAL NADA DE BASURA SOLO DESDE ABRIL Y SKOOL/` |
| **F8** | **Clases nuevas** (1-4 LB, LUCIDBOT CLASES MERCY, KALETH, ANGIE, PROMPT LUCIDBOT, COSTEO) | Mercy/Angie/Kaleth/Joaquín | `NUEVAS CLASES/` |

> Citación en este documento: `F1·C22` = curso base Clase 22 · `F0·Mód.3.1` = módulo del currículo
> SKOOL · `F0·7ma` = transcript de la 7ª clase en vivo · `F7·01-abr` = clase del 1 de abril 2026 ·
> `F8·LUCIDBOT MERCY` = clase nueva de flujo.

### 0.2 Método

1. Se digirió el **corpus completo** (las 22 clases del curso base, el currículo SKOOL y sus
   transcripts, las 10 clases de abril 2026, las 6 clases nuevas, los 2 PDFs, el Excel y las 2
   clases Calet), filtrando **solo lo que informa la FASE 0/1** (de la elección de producto a los
   6 ángulos).
2. Se leyó el **sistema real** en su fase 0/1: `buscar-producto` (skill), `ETAPA-PRODUCTO`,
   `ETAPA-1`, `ETAPA-0`, `ETAPA-1B`, `ETAPA-2`, `ETAPA-RESEARCH`, `MODULO_INTELIGENCIA_PRODUCTO`,
   `GUIA_MADRE_PARAMETRIZADA`, `ETAPA-6` (F1) y los semáforos de `ESCALADO/`.
3. Cada base de investigación se cruzó 1-a-1. Estados:

| Estado | Significa |
|---|---|
| **✓ CUBIERTO** | El sistema ya lo produce/ejecuta en F0/1 (con archivo dueño) |
| **◐ PARCIAL** | Existe pero incompleto, con otro nombre o sin campo propio |
| **✗ FALTA** | La clase lo pide y el sistema no lo tiene |

### 0.3 Pipeline F0/1 actual del sistema (el que se compara)

```
buscar-producto (F0)      RUTA A everg./B evento · flujo de demanda · 3 fuentes ·
                          descarte (saturación/margen) · ranking 5 ejes /15 · regla 10%
        ↓
etapa-producto            17 criterios (R1-R10 + O1-O4) · % aptitud 85/70 · anti-saturación ·
                          margen real ≥3 USD · proveedores en Dropy
        ↓
etapa-1                   costeo P1u/P2u/P3u · arquitectura de oferta (1/2/3 · 2x1 · 4x2 · combo afín)
        ↓
etapa-0                   clasificador de creativos: transcripciones → ángulo por video → 6 videos
        ↓
etapa-1b                  minado de VOZ DEL CLIENTE ([VOZ-REAL]/[DESEO-REAL]) · problema oculto ·
                          _VOZ_CLIENTE.csv + verificador
        ↓
etapa-2                   6 fichas de ángulo (avatar 5 ejes + conciencia 1/2/3A/3B · dolor · deseo ·
                          promesa · saturación · origen) · fanpage F1-F5
        ↘
etapa-research (opcional) módulo A: ingredientes → ángulos ocultos · módulo B: Ad Library (Apify)
                          VALIDADO/VÍRGEN
        ↓
etapa-6 (F1)              1 campaña / 6 conjuntos / 1 anuncio por ángulo (ABO)
```

---

# PARTE A — LA CLASE 22, DESNUDADA

*(F1·C22, "Optimización del Flujo de Venta y Umbral Cognitivo", instructor Joaquín — la clase de
flujo más citada por el sistema.)*

### A.1 Ficha y tesis

- **Tesis:** optimizar el flujo = **convertir más SIN gastar más en publicidad** — "el punto de
  dolor más fuerte del dropshipper".
- **Promesa concreta:** un flujo al 10% de conversión puede pasar a **15-22%** "mañana mismo".
- **Frase de cierre:** "Cada optimización los acerca a un producto más rentable, y la diferencia
  entre quienes venden y quienes no está en la **velocidad** con la que ejecutan."

### A.2 Los 10 aspectos para optimizar un flujo — y TODOS salen de la investigación de mercado

> "Sin investigación de mercado, NADA de lo que voy a nombrar tiene importancia." — Joaquín.

| # | Aspecto | Qué exige de la investigación | Fuente |
|---|---|---|---|
| 1 | **Investigación de mercado** | La base de todo; identificar el avatar | F1·C22 |
| 2 | **Comprender al cliente** | Saber a quién y cómo comunicarle | F1·C22 |
| 3 | **Puntos débiles** | El dolor activo, el síntoma concreto | F1·C22 |
| 4 | **Resultado deseado** | Punto A → punto B; el producto es el puente | F1·C22 |
| 5 | **Motivaciones** | Qué lo impulsa a comprar; qué palabras lo mueven | F1·C22 |
| 6 | **Necesidades** | Qué necesita para atacarlas en el flujo | F1·C22 |
| 7 | **Deseos** | La transformación buscada (mejor cuerpo, bajar de peso) | F1·C22 |
| 8 | **Género** | A quién va dirigido (el caso del hombre con el producto "de mujeres": al verlo en el chat, puso a un hombre sosteniéndolo y empezaron a comprarle hombres) | F1·C22 |
| 9 | **Ingresos** | Posición económica del avatar, para manejar costos/precios | F1·C22 |
| 10 | **Nivel de conciencia** | "Lo dejó de último pero es sumamente importante" | F1·C22 |

### A.3 La estructura del flujo a nivel de copies e imágenes

Joaquín la da sobre la estructura general de Mercy (video → imágenes → testimonios → audio).
Sus 4 pasos visuales:

1. **TÍTULO IMPACTANTE** — fuente grande, lo primero que se ve; la mayoría no lee, escanea títulos
   y palabras resaltadas. Nunca título y subtítulo del mismo tamaño/color. Ejemplo: "Glucosamina
   Forte 6 en 1 — desinflama el nervio ciático".
2. **BENEFICIO PRINCIPAL + RESULTADO DESEADO en la MISMA imagen** — congruente con lo pautado en
   Meta; si la persona ve algo distinto → **efecto rebote** y se sale.
3. **CÓMO LO VA A LOGRAR** — modo de uso/promesa ("con solo 2 cápsulas al día, en la primera
   semana…").
4. **PRUEBA SOCIAL con "MOMENTOS" (antes/después)** — "cómo me sentía antes y cómo me siento
   ahora"; + "me lo recomendó mi médico/tía". Sin prueba social la conversión está muy baja
   (analogía del restaurante lleno).

### A.4 Reducir fricciones + qué MATA las conversiones

**Las 3 fricciones a matar (F1·C22):**

| Fricción | Cómo se mata |
|---|---|
| "¿Y si no me funciona?" | **Garantía 30 días**: "si no te funciona, te devolvemos el 100% sin preguntas" |
| CTA débil | **CTA con BENEFICIO**, no "compra ahora" ("desinflama tu nervio ciático a partir de hoy"); en salud usar "tratamiento" y cantidades (180 cápsulas) para subir percepción de valor |
| "¿Será real?" | **Pruebas sociales con IMÁGENES**: persona tomándose/usando el producto, no solo "ya lo recibí" |

**Qué mata las conversiones (lista de la clase):** títulos aburridos o sin congruencia con Meta ·
mucho texto en una imagen (umbral cognitivo) · CTA escondido · sin testimonios/reseñas/garantías ·
imágenes de mala calidad o copiadas tal cual. Y la advertencia estratégica: **cuando la persona se
sale del flujo, Meta la bombardea con publicidad de tu competencia** — "le hacemos el trabajo a la
competencia".

**Tip de marca:** la MISMA fuente en títulos de Meta, flujo y landing → se identifica como marca
y secuencia (Joaquín trabaja 80% imágenes / 20% video). En reseñas: **menos emojis y ortografía
menos perfecta** — "es raro que una persona escriba tan perfecto".

### A.5 El umbral cognitivo

- **Definición:** la cantidad de información que el cerebro procesa de un momento dado. Si saturas
  UNA imagen con todo (beneficios, resultados, envío, contraentrega) la persona **no la procesa**.
- **Regla:** imagen clara, texto legible, **segmentado**. "A las personas solo les interesa cómo
  les vas a resolver su problema." Cada scroll del interesado = se está identificando.
- ⚠️ **Choque ya registrado (C-06):** esta clase dice "6-8 propuestas de valor"; Calet (F5) dice
  "muchas propuestas de valor, atacando todo". El sistema lo resolvió **por ubicación** (ver C.5):
  en el creativo manda el umbral cognitivo; en el bot manda la densidad. **Test T01** corriendo.

### A.6 Las propuestas de valor

- **Fórmula:** `Problema + Solución (producto) + Resultado deseado = Propuesta de valor`.
- Colocar **6-8** (en el análisis del flujo de glúteos: "a veces 10-20"), y **una junto al precio**
  en Lucid.
- Función: mostrar que el producto sirve para MUCHO más que el ángulo de entrada → sube la
  percepción de valor. Ejemplos: triglicéridos + Omega 3 → "mejorar la salud cardiovascular";
  dolor de rodilla + Bearvana → "caminar/subir escaleras sin molestias".

### A.7 Niveles de conciencia — con tabla de equivalencia (trampa de numeración)

La Clase 22 numera los niveles **al revés** que la Clase 12 y que el sistema. Tabla para no
confundirse:

| Situación del avatar | C22 dice | C12 dice | Sistema dice (`ETAPA-2`) | Cómo se le habla |
|---|---|---|---|---|
| Tiene el síntoma pero **no conoce la causa/problema** | Nivel 3 | Nivel 1 | **N1** | Educarlo primero (nombrar su problema) |
| **Sabe el problema, no la solución** | Nivel 1 | Nivel 2 | **N2** | Presentar el producto como la solución |
| Sabe el problema y el producto, **teme/no le convence** | Nivel 2 | Nivel 3 | **N3A** | Reducir fricción: autoridad, garantía, prueba social, contraentrega |
| Conoce el producto y **compara ofertas** | — | — | **N3B** | Acelerar decisión: oferta-escasez o comparación |

### A.8 Las métricas con las que C22 decide

- **Lanzar 3-4 ángulos** y ver **clics en el enlace** por ángulo (el de más clics tiene público).
- **CPM como termómetro de saturación**: CPM ~20k = ángulo muy competido; ~10k = menos saturado
  → trabajar ese (unidad COP/Colombia, `NO-PORTAR` la cifra).
- **% conversación por impresión** y **% conversación por clic en el enlace** ("la más importante,
  más que el CTR: mide quién dio clic y LLEGÓ al WhatsApp").
- **Mensaje inicial:** "Hola, quiero más información de [producto] con registro INVIMA" → más
  confianza y más probabilidad de entrar al chat.
- Optimizar el flujo **hacia el ángulo ganador** (traer al bot el ángulo con más clics).

### A.9 Mapeo de los 10 aspectos ↔ sistema (lo que pide la clase vs lo que produce la FASE 0/1)

| # | Aspecto | Estado | Dónde vive en el sistema (o qué falta) |
|---|---|---|---|
| 1 | Investigación de mercado | ✓ | `buscar-producto` + `ETAPA-1B` (voz del cliente) + `ETAPA-2` (fichas) |
| 2 | Comprender al cliente | ✓ | Ficha de avatar de `ETAPA-2`: "tan específico que alguien lo reconocería en la calle" |
| 3 | Puntos débiles | ✓ | Eje **Dolores** de `ETAPA-2` + `<banco_dolor_real>` de `ETAPA-1B` |
| 4 | Resultado deseado | ✓ | Eje **Deseos** + `Punto A → Punto B` + promesa de cada ficha |
| 5 | Motivaciones | ◐ | Vive **dentro** de deseos/frustraciones; no hay campo "motivaciones" con nombre propio (G-02) |
| 6 | Necesidades | ◐ | Ídem: cubiertas por dolor/emoción; sin listado explícito (G-02) |
| 7 | Deseos | ✓ | Eje **Deseos** + **Emoción/necesidad oculta** ("el eje que más convierte") |
| 8 | Género | ✓ | Campo `avatar_genero` por ángulo (MUJER/HOMBRE/MIXTO) |
| 9 | Ingresos | ✗ | **No existe** variable de ingresos del avatar (G-01) |
| 10 | Nivel de conciencia | ✓ | `1 / 2 / 3A / 3B` por ficha, con la tabla de equivalencia de A.7 |

**Veredicto Parte A:** la Clase 22 está implementada en el sistema en 7 de 10 aspectos; 2 quedan
parciales (motivaciones/necesidades como nombres propios) y 1 falta (ingresos). Lo demás de la
clase (estructura, fricciones, umbral, propuestas, niveles, métricas) ya tiene archivo dueño —
verificado en `PLANTILLAS_FLUJO_BOT.md` (choque C-06), `PLANTILLAS_DEFAULTS_OPERADOR.md`
(garantía), `ETAPA-4/5`, `ETAPA-7`.

---

# PARTE B — INVENTARIO MAESTRO DE BASES DE INVESTIGACIÓN DE MERCADO

*(Todo lo que las fuentes exigen investigar antes de armar ángulos y campaña, por categoría, con
fuente y estado en el sistema F0/1. Estado: ✓ / ◐ / ✗.)*

## B.1 · El avatar — demografía e identidad

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Quién es, en concreto** | "No 'mujeres' — quién, qué edad, qué problema" | F0·7ma · F1·C19 | ✓ `ETAPA-2` (avatar de calle) + `buscar-producto` ("¿quién tiene el problema? no 'todos'") |
| **Género** | Revisar ambos géneros en el chat; el creativo puede abrir el género que no consideraste | F1·C22 #8 | ✓ `avatar_genero` |
| **Edad** | Público WhatsApp: mayor (30+ / 38+), **mayor poder adquisitivo** | F0·Mód.2.5 · F0·6ta | ✓ `avatar_edad` bucket (25-35 / 35-45 / 45-60 / 60+) + banda derivada del ángulo (corrección C-05) |
| **Ingresos / posición económica** | "Para manejar los costos/precios" | F1·C22 #9 | ✗ **G-01** |
| **Plataformas que consume** | Saber qué redes consume el avatar para saber a quién mostrar el producto | F1·C12 · F1·C19 | ◐ No es campo propio; se infiere del canal (WhatsApp) y del minado |
| **Contexto/hábitos** | Agendas ocupadas, viajeros, usuarios que fallaron por inconstancia, objeciones médicas (diabetes) | F1·C10 | ✓ Descripción narrativa de la ficha ("mujer de 30-40 que lleva 3 meses en el gym…") |
| **Público WhatsApp vs Landing** | Perfil distinto: WhatsApp = mayor, desconfía de web, mayor poder adquisitivo; Landing = más joven/tecnológico | F0·8 CLASE | ✓ El sistema entero opera en clave WhatsApp/COD |

## B.2 · Psicografía del avatar — la materia prima de los ángulos

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Dolores (puntos débiles)** | El problema activo con síntoma concreto | F1·C22 #3 · F1·C12 | ✓ Eje Dolores + banco de voz real |
| **Deseos** | La transformación buscada; la investigación real tiene **20+ deseos** por producto | F1·C22 #7 · F1·C10 | ✓ Eje Deseos + `[DESEO-REAL]` |
| **Miedos** | Qué teme si no actúa (la caída del cabello como nicho de miedo) | F1·C12 | ✓ Eje Miedos |
| **Frustraciones** | Qué intentó antes sin éxito ("ya probé proteína genérica") | F1·C12 · F1·C19 | ✓ Eje Frustraciones |
| **Emoción / necesidad oculta** | La transformación de identidad detrás del dolor; **el eje que más convierte** | F1·C12 (caso ducha) | ✓ Eje Emoción + problema oculto en `ETAPA-1B`/`ETAPA-2` |
| **Motivaciones** | Qué lo impulsa a comprar; qué palabras lo mueven | F1·C22 #5 | ◐ **G-02** (vive dentro de deseos; sin campo propio) |
| **Necesidades** | Qué necesita el avatar para atacarlas en el flujo | F1·C22 #6 | ◐ **G-02** |
| **Creencias** | Un ángulo conecta con creencias del avatar | F1·C12 | ◐ No es un eje de la ficha; se cubre vía autoridad/prueba |
| **Momentos (antes → después)** | "Cómo me sentía antes y cómo me siento ahora" — convierten muchísimo | F1·C22 · F1·C7 | ✓ `ETAPA-5` (testimonios/M2) · `ETAPA-7` (momento antes→después) |
| **Nivel de conciencia** | Define cómo se le habla en anuncio y bot | F1·C22 #10 · F1·C12 · F0·4º | ✓ `1/2/3A/3B` (ver A.7) |
| **Problema oculto** | "La mina de oro": el problema que nadie nombra (metales pesados → caída de cabello) | F1·C12 · F1·C19 | ✓ `ETAPA-1B` (problema oculto) + `ETAPA-2` (componente→dolor oculto) |

## B.3 · Voz del cliente — dónde se mina

| Fuente de minado | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Reddit, foros, reseñas de Amazon, YouTube, blogs** | "La investigación de mercado es lo que perdura; se hace en Reddit, Amazon, YouTube, TikTok y foros" | F1·C19 · F1·C2 | ✓ `ETAPA-1B` (búsquedas `foro experiencias`, `testimonios blog`; regla de no fabricar voz) |
| **Comentarios de competidores (FB/IG/TikTok)** | Minar preguntas y deseos en comentarios | F1·C19 · F1·C7 | ✓ vía Módulo B de `ETAPA-RESEARCH` (Apify) — declarado en `ETAPA-1B` |
| **"¿Dónde lo compro?" en TikTok/Reels** | Señal de calle: intención explícita sin tienda que la atienda | F1·C5 · F1·C16 | ✓ `buscar-producto` §2 (señal de calle) |
| **Chats propios** | Leer los chats: si varios preguntan "¿sirve para calambres?" y sí sirve, agregarlo | F0·7 CLASE · F1·C1 | ◐ Fuerte post-cierre (`ETAPA-11`); en F0/1 solo **si hay histórico** (MODULO_INTELIGENCIA lee minado previo) |
| **Videos validados (likes/comentarios/fecha)** | Usar videos ya validados por el mercado como base del flujo y fuente de ángulos | F1·C10 · F1·C5 | ✓ `ETAPA-0` clasifica los videos que entrega el operador (la validación la hace el operador al elegirlos) |
| **Escuchar el anuncio ganador y sacarle ángulos** | "Escucho el audio del video y de ahí saco ángulos de venta y los plasmo en una imagen" | F4 · F1·C10 | ✓ `ETAPA-0` (ángulo por video) + `ETAPA-3` (microángulos del ángulo ganador) |

## B.4 · Competencia y saturación

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Biblioteca de Anuncios: regla del 10%** | nº anuncios ÷ 10 ≈ nº tiendas; **>20 tiendas no meterse** salvo ángulo virgen o canal WhatsApp | F1·C5 · F0·7ma | ✓ `buscar-producto` §3 + excepción "ángulo virgen escrito" + `ETAPA-PRODUCTO` |
| **Búsqueda top-down: problema, no producto** | Buscar un problema en la Ad Library → "todos los países" → ver quién lo ataca en GT/CO → buscar el producto | F7·01-abr | ◐ La señal existe (`buscar-producto`: "se busca gente con un problema"), pero el barrido multi-país no está como paso (**G-06**) |
| **Google Trends de estacionalidad** | Verificar pico recurrente 2-5 años → demanda predecible (evergreen) | F7·01-abr · F1·C5 | ◐ Existe **solo en RUTA B** (ventana de evento); falta el check en RUTA A (**G-05**) |
| **CPM como señal de saturación** | CPM alto = audiencia saturada o mal ángulo; CPM 20k vs 10k | F1·C7 · F0·7ma | ✓ `03_SENALES_DECISION.md` (nota CPM cualitativa) · `ETAPA-7` ("CPM→ángulo saturado") |
| **Nº de proveedores por producto (Dropy) = saturación** | Regla de pocos proveedores; scroll aleatorio castiga a los saturados; <6-7 ideal, >10 con pinzas | F1·C16 | ✓ `ETAPA-PRODUCTO` (contar a mano + regla anti-saturación) |
| **"Validados pero sin escalar"** | Productos con ventas reales que nadie escala: 7d 10-120, 30d 120-500, stock 80; "creado hace <1 mes y ya vendiendo" | F1·C16 | ✓ Regla adoptada ("preferir validados sin escalar", citada en `ETAPA-PRODUCTO`); los filtros finos son de Drop Killer (pago) |
| **Productos que se "queman" son ÁNGULOS, no productos** | "Si todos venden con un ángulo, busca otro"; el mismo producto tiene N ángulos | F1·C8 · F0·8 CLASE · F1·C19 | ✓ Es la premisa del sistema (6 ángulos por producto + rotación en `ETAPA-7`) |
| **Suite de espionaje TikTok** | Scalbus con Kalodata, FastMoss, Minea (+ Drop Killer, Asparo) y AdSpy para FB; filtros 7d/30d, >10k artículos, >1.000 ventas, últimas páginas | F8·LUCIDBOT MERCY (mód. búsqueda) · F0·Mód.3.1 | ✗ **G-03** (el sistema usa Ad Library + Dropy; no hay capa TikTok) |
| **Store Radar / Ad Killer** | Escrapear tiendas de otros países y ver anuncios nuevos por keyword | F1·C16 | ✗ No implementado (herramientas de Drop Killer; el MCP de Drop Killer fue anunciado pero no existe aún) |
| **Precio de la competencia** | Subir precio gradual observando competidores; igualar o superarlos | F0·8 CLASE · F1·C17 | ◐ `ETAPA-1` usa "investigación web" para el costeo; sin paso formal de barrido de precios |
| **Anuncio de fanpage joven / 250 anuncios** | "250 anuncios activos → al menos 125 ventas"; ratio 1/3 vendedores→venta | F0·6 CLASE | ✓ Referenciado en `ETAPA-6/7` (producción de réplicas) |

## B.5 · Demanda y producto (el scope de F0 del sistema)

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Flujo de demanda primero** | "No se buscan productos; se busca gente con un problema activo" — y "¿por qué AHORA?" | F7·01-abr · F1·C5 | ✓ `buscar-producto` §1 (obligatorio, ambas rutas) |
| **Tres fuentes mínimo** | Barrido multifuente para no sesgar (calle / catálogo / competencia) | F1·C5 | ✓ `buscar-producto` §2 (mínimo 3) |
| **Ordenar catálogo por NUEVO, no por top** | No copiar el más vendido; lo más vendido ya está saturado | F1·C16 · F1·C5 | ✓ `buscar-producto` §2 + `ETAPA-PRODUCTO` |
| **17 criterios de validación** | Los 4 decisivos (problema, stock, ligero/no frágil, proveedor) + obligatorios + recomendados; aptitud 85% lanzar / <70% no | F1·C5 | ✓ `ETAPA-PRODUCTO` (R1-R10 + O1-O4 + % aptitud) |
| **Margen real ≥3 USD tras gastos** | Después de publicidad, herramientas, administrativos, devoluciones | F1·C5 · F2 | ✓ `ETAPA-PRODUCTO` + `ETAPA-1` (costeo) |
| **Tipos de producto: impulso / evergreen / micronicho** | Elegir según etapa del operador; nuevos → impulso ticket bajo | F1·C5 | ✓ `buscar-producto` (RUTA A evergreen / B evento) + arquitectura de oferta por tipo en `ETAPA-1` |
| **No mercado tradicional** | Si está en farmacia/súper/esquina, la gente lo compra allá | F1·C5 | ✓ Descarte en `buscar-producto` §3 |
| **Stock ilimitado (llamar al proveedor)** | Aunque Dropy muestre pocas unidades, puede ser laboratorio | F1·C5 | ✓ Criterio O1 + conteo de proveedores `ETAPA-PRODUCTO` |
| **Proveedor verificado/premium** | Calificación Dropy + señales (contesta rápido, fotos reales, PDF) | F1·C5 | ✓ Criterio O3 |
| **Combo con productos del MISMO proveedor** | Armar combos sin doble flete; un combo elimina competencia | F1·C5 #13 | ◐ `ETAPA-1` maneja "combo afín" como arquitectura de oferta; **no** es criterio de sourcing en F0 (**G-07**) |
| **Track record del producto en Dropy** | "Productos súpervirales cuyo target tiene récord negativo en Dropy" → cancelaciones altas | F7·22-abr | ✗ **G-04** |
| **Validación por clics del ángulo** | 20-40 clics en el enlace = "Meta te dice que ese ángulo es ganador" | F1·C7 · F0·Mód.3.1 | ✓ Lectura de F1 (`ETAPA-7` + semáforos) |
| **Test de 3-4 ángulos simultáneos** | Elegir ángulos por clics/conversiones, no por gusto | F1·C20 · F0·Mód.3.1 | ✓ 6 ángulos en F1 (1 anuncio por ángulo) |
| **Validación en fanpage propia (orgánico)** | Publicar el creativo en la fanpage antes de pautarlo | F0·8 CLASE | ◐ No es paso formal del pipeline |

## B.6 · Ángulos — construcción

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Definición operativa** | Perspectiva estratégica para hacer el producto relevante y deseable a UN cliente específico; conecta con deseos, dolores, emociones, creencias, aspiraciones, miedos, necesidades ocultas | F1·C12 · F1·C20 | ✓ `ETAPA-2` (ficha) + `reglas-sistema` skill |
| **Taxonomía completa (15-16 tipos)** | problema-dolor · solución · resultado · miedo · ahorro · rapidez · educativo · mecanismo único · autoridad · prueba social · error común · comparación · emocional · facilidad · garantía · oferta-escasez | F0·Mód.3.1 · F1·C20 | ✓ Banco literal en `ETAPA-2` (16 tipos) |
| **Un creativo = UN ángulo dominante** | No mezclar ángulos; el cliente se pierde | F1·C20 · F1·C22 | ✓ 6 fichas = 6 ángulos, 1 anuncio por ángulo |
| **Cómo ELEGIR el ángulo** | Problema urgente→problema-solución/miedo · competencia fuerte→comparación/mecanismo · poca confianza→autoridad/garantía · aspiracional→emocional/resultado | F1·C20 | ✓ `ETAPA-2` reproduce estas reglas |
| **Ángulo emocional priorizado** | "El mejor de todos"; la emoción vende más que cualquier otra parte | F0·Mód.3.1 · F1·C12 | ✓ Eje Emoción "el que más convierte" + ranking de `ETAPA-2` |
| **Problema oculto desde ingredientes** | Pedir a Claude: ingredientes → qué soluciona cada uno → ángulos | F1·C10 | ✓ `ETAPA-RESEARCH` Módulo A + `ETAPA-2` componentes |
| **Fórmula HPPPC** | Hook + Problema + Promesa + Prueba + CTA para pasar de ángulo a anuncio | F1·C20 | ✓ Arquitectura de copy de `ETAPA-4` (hook 3s + cuerpo) |
| **Hook con números/credibilidad** | "Según el DANE, el 45%…" — números reales, nunca inventar | F1·C12 | ✓ `ETAPA-2`: "Hook con número… solo cifras reales" |
| **Testimonio como formato campeón** | "TESTIMONIOS funcionando súper bien" + casos con capturas | F1·C7 · F1·C22 | ◐ El tipo "prueba social" existe en el banco y el testimonio se usa en el bot (F2+) y en copies F4; **no hay regla de prioridad ni captura temprana de testimonios** en F1 (**G-08**) |
| **Lenguaje de apoyo (no "cura")** | "Contribuye, acompaña, puede mejorar"; nunca promesas absolutas → políticas Meta | F1·C20 | ✓ Compliance en ads (`reglas-sistema`, plantillas) |

## B.7 · Oferta, valor y transformación

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Transformación en 4 planos** | Estética / funcional (fácil) / emocional / combinada | F1·C10 | ✓ Promesa + "Punto A→B" + ejes emoción/facilidad en las fichas |
| **Hablar en DÍAS, no meses** | "12-16 días" se percibe fácil; "6-10 meses" eterno | F1·C10 · F1·C7 | ✓ Plantillas de flujo (tiempos creíbles post-cierre); en F1 el ángulo no promete tiempos |
| **Transformación creíble (día 21/28)** | Ni "7 días 20 kg" ni "1 año" | F1·C7 | ✓ `PLANTILLAS_FLUJO_BOT.md` / plantillas de testimonios |
| **Muchos beneficios (10-30) suben percepción de valor** | Imagen de beneficios DESPUÉS del punto de dolor | F1·C7 · F1·C10 · F5 | ✓ `ETAPA-4` (infografías) + `ETAPA-5` propuestas de valor + `PALANCA_1` (F5) |
| **Agregar valor, NO bajar precio** | "La gente compra transformación" | F1·C7 | ✓ Doctrina de oferta `ETAPA-1` + plantillas |
| **Framing "tratamiento", no "frasco"** | 1/2/3 tratamientos; cantidades (90/180/270 cápsulas); "la más elegida" | F1·C10 · F1·C7 | ✓ `ETAPA-1` (matriz 1/2/3 · 2x1 · 4x2 · combo) consume bot/etapa-6 |
| **P2u la más irresistible** | La opción 2 es la que la mayoría elige | F0·Mód.2.3 · F1·C17 | ✓ Doctrina de escalera de precios `ETAPA-1` |
| **Garantía 30 días / reducir fricción** | Mata la objeción "¿y si no me funciona?" | F1·C22 | ✓ `PLANTILLAS_DEFAULTS_OPERADOR.md` `[GARANTIA]` |
| **Sellos, tiempos de entrega, componentes** | "Tu pedido llega en 1-3 días" en grande; el interesado lee componentes | F1·C7 | ✓ Plantillas de flujo (sellos) + componentes en ficha |
| **Misma fuente en Meta/flujo/landing** | Identidad de marca; "secuencia" | F1·C22 | ✓ `ETAPA-4` ("misma fuente… e infografías") |

## B.8 · Objeciones

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Excel de objeciones vs medios** | Listar TODAS las objeciones; cada una resuelta en video/imagen/testimonio/audio; revisar chats para nuevas objeciones | F1·C1 · F0·Mód.2.5 | ✓ `ETAPA-5` (cascada T1-T4 + FAQ) y `MODULO_INTELIGENCIA_PRODUCTO` (objeciones); en F0/1: insumo del brief |
| **Liberar objeciones en el audio** | "Dentro de mi investigación ya sé qué objeciones dará; las libero en el audio" | F0·7ma · F1·C7 | ✓ `ETAPA-5` (audio de 50-60s) |

## B.9 · Métricas de validación (la investigación que sigue tras lanzar)

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **% conversación por impresión** | Conversaciones ÷ impresiones; termómetro temprano | F1·C7 · F0·Mód.5.2 | ✓ `03_SENALES_DECISION.md` (🔴<1.5 · 🟡1.5-3.49 · 🟢≥3.5) — calibración propia |
| **% conversación por clic en enlace** | "LA MÁS IMPORTANTE, más que el CTR": quién LLEGÓ al WhatsApp | F1·C7 · F1·C22 | ✓ `03_SENALES_DECISION.md` (🔴<35% · 🟡35-49% · 🟢50-70%) |
| **CTR** | <1 malo · 1-2 regular · 2-4 bueno · 4+ excelente; en video <1.5 → cambiar hook | F0·Mód.5.4 · F1·C7 | ✓ Semáforos propios de `ESCALADO/` |
| **CPM** | Bueno 7-10k COP; 17-20k alto; señal de saturación | F1·C7 · F0·7ma | ✓ Nota cualitativa (GT usa Q) en `03_SENALES_DECISION.md` |
| **Frecuencia** | 1.5-1.8 = saturando; 2-3 con CPM alto → apagar o duplicar con +presupuesto | F1·C7 | ✓ Gestión de fatiga en `ETAPA-7/10` (ventanas propias) |
| **CPA semanal ponderado + CPA real sobre entregados** | No juzgar el día; sumar semana ÷ gasto; CPA aparente → real (100→70→60) | F0·8 CLASE · F1·C8 | ✓ Doctrina de escalado (`00_INTRO_FILOSOFIA` la mantiene vigente) |
| **Efectividad de entregas (85%)** | +2 puntos = dinero grande al mes; variable de negocio | F0·8 CLASE | ◐ Se mide post-cierre (LucidSales); no en F0/1 |
| **250 anuncios → 125 ventas** | Ejército de anuncios tras validar ángulo | F0·6 CLASE | ✓ `ETAPA-6/7` (réplicas R[N]) |
| **⚠️ Choque de escalas de mentores** | SKOOL Mód.5.2 usa 0.3/0.5/0.8/1-1.5% y 10/20/30/40%; Joaquín C7 usa 1.5/2.5/3.5/4.5% y 35-70% | F0 vs F1 | ⚠️ **NC-01** — el sistema ya tiene su calibración propia; no cambiar sin data (ver C.5) |

## B.10 · Logística y operación (variables que la clase investiga antes)

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Ligero y no frágil; tamaño moderado** | Flete y garantías | F1·C5 | ✓ `buscar-producto` descarte + `ETAPA-PRODUCTO` O2/R8 |
| **Sin variaciones complejas** | Tallas/colores → devoluciones y errores | F1·C5 | ✓ Criterio R9 |
| **No de temporada** | Vender todo el año (salvo RUTA B declarada) | F1·C5 | ✓ Criterio O4 |
| **Cancelaciones: 9-10% aceptable; 20-25% alerta** | Investiga el CAUSA: puede ser target equivocado; cambiar el ángulo puede cambiar las cancelaciones (caso almohadilla → "crece 2 cm") | F7·22-abr | ✗ **G-04/G-09** (no hay métrica de cancelación ni lectura por ángulo) |
| **Cobertura/transportadora del mercado** | Adaptar transportadora y tiempos al país | F1·C8 (GT se adapta en costeo/logística) | ◐ En `ETAPA-1`/logística; no como criterio F0 |

## B.11 · Países y expansión

| Variable | Qué pide la clase | Fuente | Sistema F0/1 |
|---|---|---|---|
| **Problemas universales / multi-país** | "El mismo problema que existe en Colombia existe en Perú, Chile, EE.UU." → Ad Library "todos los países" antes de mirar GT/CO | F7·01-abr · F1·C12 | ◐ **G-06** (la Ad Library del sistema mira "el país") |
| **CPM/CPC de referencia por país** | Al entrar a un país nuevo, campaña de prueba o pedir métricas | F1·C7 | ◐ Conocimiento del operador; sin tabla en el sistema |

---

# PARTE C — DIAGNÓSTICO: SISTEMA HOY vs CLASES

### C.1 Qué corre hoy la FASE 0/1 (lectura del pipeline)

1. **`buscar-producto`** (skill F0) — RUTA A/B declarada, flujo de demanda ("¿por qué AHORA?"),
   mínimo 3 fuentes (calle/catálogo/competencia), descarte sin piedad (saturación >10 proveedores,
   >20 tiendas con regla del 10%, mercado tradicional, frágil/pesado, variaciones, sin stock),
   ranking 5 ejes /15 y excepción única de saturación ("ángulo virgen escrito").
2. **`etapa-producto`** — 17 criterios (R1-R10 + O1-O4), % de aptitud 85/70, conteo a mano de
   proveedores en Dropy, regla anti-saturación (Clase 16), margen real ≥3 USD (Clase 5), manual
   primero y "no inventar datos de mercado".
3. **`etapa-1`** — costeo P1u/P2u/P3u GT y arquitectura de oferta (1/2/3 · 2x1 · 4x2 · combo afín).
4. **`etapa-0`** — clasificador de creativos: transcripciones TXT → ángulo por video (regla de los
   primeros 5 segundos) → 6 videos.
5. **`etapa-1b`** — minado de voz del cliente ([VOZ-REAL]/[DESEO-REAL], problema oculto), con
   `verificar_voz.py` y registro en `_VOZ_CLIENTE.csv`; regla de no fabricar testimonios.
6. **`etapa-2`** — 6 fichas de ángulo: avatar de 5 ejes + nivel de conciencia, dolor, deseo,
   promesa, saturación, **origen obligatorio** (cita de dónde sale), ranking de 5 criterios y
   asignación de fanpage F1-F5.
7. **`etapa-research`** (opcional) — Módulo A: ingredientes/componentes → ángulos ocultos.
   Módulo B: Ad Library vía Apify (VALIDADO/VÍRGEN).
8. **`etapa-6` (F1)** — 1 campaña / 6 conjuntos / 1 anuncio por ángulo, ABO, presupuesto igual,
   hora 4 AM, réplicas R[N].

### C.2 GAPS — lo que las clases piden y el sistema no tiene (o tiene parcial)

> **G-01 · Ingresos del avatar** *(F1·C22 #9)* — ✗ FALTA. No existe variable de ingresos/posición
> económica en la ficha de avatar. Es el único de los 10 aspectos de la Clase 22 sin equivalente.
> Impacto: calibrar precio y arquitectura de oferta al poder adquisitivo (sobre todo en GT).
>
> **G-02 · Motivaciones y necesidades como campos explícitos** *(F1·C22 #5-6)* — ◐ PARCIAL. Están
> cubiertas funcionalmente dentro de deseos/frustraciones/emoción, pero no como listado nombrado.
> Impacto bajo; es más un tema de nomenclatura de la ficha que una capacidad ausente.
>
> **G-03 · Suite de espionaje TikTok** *(F8·LUCIDBOT MERCY mód. búsqueda: Scalbus → Kalodata ·
> FastMoss · Minea · Asparo; AdSpy para FB; F0·Mód.3.1)* — ✗ FALTA. El sistema espía en Meta
> (Ad Library/Apify) y catálogo (Dropy), pero no tiene la capa TikTok (donde "lo nuevo sale
> primero" — F1·C5). Impacto: descubrimiento de ángulos y productos nuevos (módulo de búsqueda de
> productos de las clases nuevas, con filtros 7d/30d y "últimas páginas").
>
> **G-04 · Track record del producto en Dropy (historial de cancelaciones/entregas)** *(F7·22-abr)*
> — ✗ FALTA. `ETAPA-PRODUCTO` cuenta proveedores en Dropy, pero no consulta el récord de
> cancelaciones del producto/target ("productos súpervirales cuyo target tiene récord negativo en
> Dropy"). Impacto: filtro de calidad de entrega ANTES de invertir.
>
> **G-05 · Google Trends en RUTA A (evergreen)** *(F7·01-abr · F1·C5)* — ◐ PARCIAL. Existe solo en
> RUTA B (la curva del evento es la ventana). Falta el check de estacionalidad recurrente
> (pico 2-5 años → demanda predecible) para la búsqueda evergreen.
>
> **G-06 · Barrido multi-país en la Ad Library** *(F7·01-abr: "todos los países" → después GT/CO;
> F1·C12: "Colombia, Ecuador, otros países")* — ◐ PARCIAL. El flujo de demanda existe, pero la
> Ad Library del sistema consulta "el país". Impacto: ver cómo se ataca el problema globalmente
> antes de validar localmente.
>
> **G-07 · Combo multi-producto del mismo proveedor** *(F1·C5 #13)* — ◐ PARCIAL. `ETAPA-1`
> construye "combo afín" como arquitectura de OFERTA (2x1/4x2), pero el criterio de SOURCING
> ("buscar otros productos del mismo proveedor, no mezclar proveedores por el doble flete") no es
> parte de la validación F0.
>
> **G-08 · Testimonio/momentos como prioridad en F1** *(F1·C7 "testimonios funcionando súper bien";
> F1·C22 momentos; F1·C10 reseñas antes/después)* — ◐ PARCIAL. El tipo "prueba social" está en el
> banco de `ETAPA-2` y el testimonio aparece en el bot (F2+) y en copies F4, pero no hay regla de
> prioridad ni fuente de captura temprana de testimonios reales (chats/capturas) en F0/1.
>
> **G-09 · Cancelación como señal de ángulo/target** *(F7·22-abr)* — ✗ FALTA. No hay métrica de
> cancelación en ningún punto (verificado: 0 menciones en agentes/skills). La clase lo usa incluso
> para CAMBIAR ÁNGULO (almohadilla para talones → "crece 2 cm"). Impacto: F2/F4B (lectura) y
> re-lectura de F0 (target mal elegido).
>
> **G-10 · Logística de pre-selección ampliada** *(F0·8 CLASE: efectividad de entregas 85%, CPA real
> sobre entregados; F1·C5: criterios físicos)* — ◐ PARCIAL. O2 (ligero/no frágil) y R8 (tamaño)
> existen; faltan variables operativas GT (peso exacto/flete, efectividad por transportadora,
> cobertura) como criterio F0.

**Resumen cuantitativo:** de **87 bases** inventariadas en la Parte B, **✗ FALTA = 4**
(G-01 · G-03 · G-04 · G-09) y **◐ PARCIAL = 6** (G-02 · G-05 · G-06 · G-07 · G-08 · G-10);
el resto está ✓ CUBIERTO con archivo dueño.

### C.3 "No-gaps" verificados (cosas que parecían faltar y NO faltan)

Correcciones a creencias previas, verificadas contra archivo:

1. **% conversación por impresión** — SÍ existe y está **calibrada con data propia**:
   `03_SENALES_DECISION.md` (🔴<1.5 · 🟡1.5-3.49 · 🟢≥3.5) + `ETAPA-7` + `10_METRICAS_TESTEO.md`.
   No es gap. (Lo que sí queda es la **nota de escalas NC-01** vs los mentores.)
2. **Umbral cognitivo (Clase 22)** — adoptado (M-D13) y resuelto POR UBICACIÓN en
   `PLANTILLAS_FLUJO_BOT.md`: en el creativo manda el umbral; en el bot manda la densidad
   (choque C-06, con T01 corriendo).
3. **6-8 propuestas de valor (y más)** — implementadas en `ETAPA-5` (PALANCA_1 del cierre) y las
   infografías del bot.
4. **Misma fuente en Meta/flujo/infografías** — escrito en `ETAPA-4` (cita Clase 22).
5. **Emojis casi cero / humanización de reseñas** — en `ETAPA-5` ("un testimonio impecable suena a
   actriz").
6. **CPM → ángulo saturado** — en `03_SENALES_DECISION.md` y `ETAPA-7`.
7. **250 anuncios / fanpage (regla del ejército)** — referenciado en `ETAPA-6/7`.
8. **Imagen de beneficios · audios · testimonios en el flujo** — `ETAPA-4/5` (plantillas).
9. **Objeciones (Excel P1 · liberar en audio)** — cascada T1-T4 + FAQ en `ETAPA-5`.
10. **Nivel de conciencia** — `1/2/3A/3B` en `ETAPA-2` (con la trampa de numeración C22 resuelta en A.7).
11. **"El creativo es la segmentación" / segmentación por palabras** — `ETAPA-2` + `CLAUDE.md`
    (sin intereses configurados; el copy segmenta).
12. **Regla del 10% y anti-saturación** — `buscar-producto` + `ETAPA-PRODUCTO` (citas a Clases 5/16).

### C.4 Fortalezas del sistema que las clases no tienen (no tocar)

- **Origen obligatorio y trazabilidad:** cada ángulo cita de dónde sale; cada afirmación metodológica
  tiene fuente e ID (este ecosistema `_CONOCIMIENTO`).
- **Voz del cliente verificable:** `verificar_voz.py` + `_VOZ_CLIENTE.csv` + regla de no fabricar
  testimonios — las clases piden investigar; el sistema lo audita.
- **Gate de la excepción de saturación:** "sin ángulo virgen escrito, no hay excepción" (la
  Clase 5 lo dice; el sistema lo vuelve escribible).
- **Penalizaciones y descartes automáticos:** margen real, aptitud %, anti-saturación con conteos.
- **La "tabla de equivalencia" de conciencia** ya resuelta (evita el error de numeración de C22).

### C.5 Choques de fuentes que tocan F0/1 (heredados de `MATRIZ_METODOLOGIA.md` + 1 nuevo)

| ID | Choque | Estado actual |
|---|---|---|
| **C-05** | Andrómeda (segmentación amplia) vs banda de edad por avatar | Resuelto con data propia (APR-060); la banda se deriva del avatar |
| **C-06 · T01** | Umbral cognitivo (C22) vs "muchas propuestas de valor" (Calet F5) | Resuelto por ubicación (creativo vs bot); **test T01 corriendo** (`_TESTEOS.csv`, variantes ligera/densa/colage) |
| **M-D13 / M-D14** | Tensión umbilical del mismo tema en la matriz (densidad) | Se cierra con el resultado del T01 |
| **M-G01** | La métrica real es % conversación por clic (35-70%), no el CTR | Adoptado en semáforos |
| **M-F02** | Optimizar flujo = convertir más sin gastar más (10→15-22%) | Adoptado con ejecutor (`etapa-11` mide, `etapa-5` redacta) |
| **NC-01 (nuevo)** | Escalas de los mentores divergen: SKOOL Mód.5.2 (0.3/0.5/0.8/1-1.5% · 10/20/30/40%) vs Joaquín C7 (1.5-4.5% · 35-70%) | **No es gap del sistema** (ya calibrado con data propia); es un choque **documental** a registrar en la MATRIZ. Mientras no haya data GT propia por producto que lo contradiga, no se tocan los umbrales |

### C.6 Pendientes documentales (calidad de fuentes, no del sistema)

1. **2 archivos de abril truncados en origen:** `8 DE ABRIL 2026.txt` y `BRUTA\22 de ABRIL 2026.txt`
   (el procesado de 22-abr sí está completo).
2. **SKOOL consolidado parcial:** `SKOOL CLASES 2026.txt` salta de Mód.3.1 a Mód.5.1 y anuncia un
   "módulo de búsqueda de productos" que vive en `LUCIDBOT CLASES MERCY` (F8) — ya digerido.
3. **Transcripts SKOOL 4ta/5ta clase:** tramos pendientes (~25% y ~70%). No bloquea: sus resúmenes
   ya están en el dossier.
4. **Drop Killer MCP:** anunciado en la Clase 16 ("~2 semanas"); al cierre de este informe no
   existía. Si sale, re-evaluar G-03/G-04 (conexión directa de ventas/ángulos).
5. **Lucid Sales prometió módulo de investigación de mercado** (C10/C4/C19 lo mencionan): cuando
   salga, comparar contra el módulo de research propio (que ya lo reemplaza parcialmente).

---

## ANEXO — CORPUS ANALIZADO (para auditoría)

| Bloque | Archivos | Estado |
|---|---|---|
| Curso base (F1) | Clases 1-22 completas + Calet 16/22-ago | ✔ digerido (+ revisión profunda de C22, C10, C12, C20, C5, C16, C7 en este informe) |
| SKOOL (F0) | Currículo consolidado + 6ta/7ma/8va (transcripts) + resúmenes 4-9 | ✔ digerido (anexo de 8 secciones integrado a la Parte B) |
| Abril 2026 (F7) | 10 clases procesadas + brutas | ✔ digerido (2 truncados en origen — C.6) |
| Clases nuevas (F8) | CLASE 1-4 LB · LUCIDBOT CLASES MERCY · KALETH · ANGIE · PROMPT LUCIDBOT · CLASE 3 LB COSTEO | ✔ 6/6 digeridas (módulo búsqueda productos incluido) |
| Excel/PDFs (F2/F3) | Herramienta Validación · PDF Creativos · PDF Análisis Competencia | ✔ referenciados |
| Sistema | `.claude/agents/ETAPA-0/1/1B/2/PRODUCTO/6/7` · skills `buscar-producto`/`fase-1-angulos`/`regenerar-conceptos` · `DOCTRINA/ETAPA-RESEARCH` `MODULO_INTELIGENCIA_PRODUCTO` `GUIA_MADRE_PARAMETRIZADA` `ESCALADO/*` `PLANTILLAS_*` | ✔ leído en F0/1 + greps de verificación |

**Regla final de este documento:** nada de lo aquí listado como GAP se implementa sin decisión del
operador. Este archivo diagnostica; la matriz decide y las etapas ejecutan.
