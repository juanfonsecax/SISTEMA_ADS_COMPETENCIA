from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .config import CATALOG_CONCEPTS
from .util import canonical_json, sha256_file, sha256_text, utc_now

TAXONOMY_VERSION = "1.0.0"
TAXONOMY_SOURCE = (
    "Blueprint_Maestro_Inteligencia_Creativa_Ads_v1.md#8.1; "
    "_CATALOGO_CONCEPTOS.md; Phase 3 scope"
)
BLUEPRINT_SECTION = "8.1"

CANONICAL_CONCEPT_KEYS = tuple(
    key for key in CATALOG_CONCEPTS if key != "SIN_CLASIFICAR"
)

DIMENSIONS: tuple[dict[str, Any], ...] = (
    {
        "dimension": "avatar",
        "label": "Avatar / segmento",
        "definition": "Persona o grupo concreto al que se dirige el mensaje.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 10,
    },
    {
        "dimension": "nivel_conciencia",
        "label": "Nivel de conciencia",
        "definition": "Que sabe el destinatario sobre problema, solucion o producto.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 20,
    },
    {
        "dimension": "problema",
        "label": "Problema",
        "definition": "Friccion o situacion que se presenta.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 30,
    },
    {
        "dimension": "deseo",
        "label": "Deseo / resultado",
        "definition": "Estado que el comprador busca.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 40,
    },
    {
        "dimension": "emocion",
        "label": "Emocion",
        "definition": "Estado emocional que la pieza activa o promete resolver.",
        "blueprint_section": "Phase 3 scope",
        "primary_required": True,
        "sort_order": 50,
    },
    {
        "dimension": "angulo",
        "label": "Angulo",
        "definition": "Razon de compra prioritaria que se argumenta.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 60,
    },
    {
        "dimension": "idea_central",
        "label": "Idea central",
        "definition": "Observacion o premisa que organiza la pieza.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 70,
    },
    {
        "dimension": "concepto",
        "label": "Concepto creativo",
        "definition": "Recurso narrativo o persuasivo que expresa la idea.",
        "blueprint_section": "8.2; _CATALOGO_CONCEPTOS.md",
        "primary_required": True,
        "sort_order": 80,
    },
    {
        "dimension": "formato",
        "label": "Formato",
        "definition": "Estructura comunicativa.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 90,
    },
    {
        "dimension": "estilo",
        "label": "Estilo visual",
        "definition": "Tratamiento estetico.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 100,
    },
    {
        "dimension": "composicion",
        "label": "Composicion",
        "definition": "Organizacion espacial.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 110,
    },
    {
        "dimension": "hook",
        "label": "Hook",
        "definition": "Modo de iniciar la atencion.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 120,
    },
    {
        "dimension": "mecanismo",
        "label": "Mecanismo",
        "definition": "Como explica la solucion o su funcionamiento.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 130,
    },
    {
        "dimension": "tipo_prueba",
        "label": "Prueba / evidencia",
        "definition": "Evidencia que sustenta la promesa.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 140,
    },
    {
        "dimension": "objecion",
        "label": "Objecion",
        "definition": "Barrera que la pieza intenta resolver.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 150,
    },
    {
        "dimension": "oferta",
        "label": "Oferta",
        "definition": "Intercambio comercial propuesto.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 160,
    },
    {
        "dimension": "cta",
        "label": "CTA",
        "definition": "Accion solicitada.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": True,
        "sort_order": 170,
    },
    {
        "dimension": "contexto_embudo",
        "label": "Contexto de embudo",
        "definition": "Papel dentro del recorrido.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 180,
    },
    {
        "dimension": "riesgo_cumplimiento",
        "label": "Riesgo de cumplimiento",
        "definition": "Posible problema legal o de plataforma.",
        "blueprint_section": BLUEPRINT_SECTION,
        "primary_required": False,
        "sort_order": 190,
    },
    {
        "dimension": "idioma",
        "label": "Idioma",
        "definition": "Codigo o idioma del anuncio cuando se conoce.",
        "blueprint_section": "Phase 3 scope",
        "primary_required": True,
        "sort_order": 200,
    },
    {
        "dimension": "mercado",
        "label": "Mercado",
        "definition": "Mercado geografico o pais objetivo cuando se conoce.",
        "blueprint_section": "Phase 3 scope",
        "primary_required": True,
        "sort_order": 210,
    },
)

CANONICAL_DIMENSIONS = tuple(item["dimension"] for item in DIMENSIONS)

_CONCEPT_DEFINITIONS = {
    "C1_OFERTA": "El precio o la cantidad es el creativo; el numeral o el precio domina la pieza.",
    "C2_BENEFICIOS": "Pregunta de dolor y beneficios explicados con iconos; el producto ocupa el centro.",
    "C3_SINTOMA": "La zona del cuerpo que duele aparece senalada; poco texto y foco en el sintoma.",
    "C4_TRANSFORMACION": "Antes y despues del mismo sujeto en dos estados.",
    "C5_PRUEBA": "Muestra realidad en vez de afirmarla: testimonio, captura, UGC o unboxing.",
    "C7_DESEO": "El cuerpo o estado deseado, no el dolor; el modelo encarna el resultado.",
    "C8_PROGRESION": "Tres o cuatro estados en el tiempo que explican el mecanismo y la progresion.",
    "C9_COMPARACION": "Dos columnas contrapuestas: lo malo frente a lo bueno.",
    "SIN_CLASIFICAR": "Fila historica sin concepto canonico asignado.",
}

DIMENSION_TAGS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "avatar": (
        ("comprador_primerizo", "Comprador primerizo", "Persona que compra por primera vez."),
        ("hogar_con_ninos", "Hogar con ninos", "Hogar con menores a cargo."),
        ("propietario", "Propietario", "Persona que posee el espacio o producto."),
        ("profesional", "Profesional", "Perfil con ocupacion o expertise especifico."),
    ),
    "nivel_conciencia": (
        ("no_consciente", "No consciente", "Aun no reconoce el problema."),
        ("consciente_problema", "Consciente del problema", "Reconoce el problema, no la solucion."),
        ("consciente_solucion", "Consciente de la solucion", "Conoce la categoria de solucion."),
        ("consciente_producto", "Consciente del producto", "Conoce el producto o marca."),
        ("muy_consciente", "Muy consciente", "Conoce producto, oferta y objeciones."),
    ),
    "problema": (
        ("confusion", "Confusion", "No sabe que elegir o como usarlo."),
        ("coste", "Coste", "El precio o gasto es la friccion."),
        ("demora", "Demora", "El tiempo de espera o resultado es la friccion."),
        ("incomodidad", "Incomodidad", "Malestar fisico o funcional."),
        ("riesgo_percibido", "Riesgo percibido", "Miedo a que no funcione o tenga efectos."),
    ),
    "deseo": (
        ("control", "Control", "Sentir dominio sobre el problema o resultado."),
        ("simplicidad", "Simplicidad", "Resolver con menos pasos o esfuerzo."),
        ("ahorro", "Ahorro", "Conservar dinero o recursos."),
        ("confianza", "Confianza", "Sentir seguridad en la decision."),
        ("comodidad", "Comodidad", "Mayor bienestar o facilidad."),
    ),
    "emocion": (
        ("frustracion", "Frustracion", "Molestia por el problema o intentos fallidos."),
        ("esperanza", "Esperanza", "Expectativa positiva de mejora."),
        ("miedo", "Miedo", "Temor a consecuencias o riesgos."),
        ("alivio", "Alivio", "Sensacion de resolver una carga."),
        ("aspiracion", "Aspiracion", "Deseo de alcanzar un estado mejor."),
        ("confianza", "Confianza", "Seguridad emocional en la promesa."),
    ),
    "angulo": (
        ("ahorro_tiempo", "Ahorro de tiempo", "Reduce tiempo o esfuerzo."),
        ("tranquilidad", "Tranquilidad", "Reduce preocupacion o riesgo."),
        ("control", "Control", "Permite dominar el problema."),
        ("facilidad", "Facilidad", "Hace simple una tarea compleja."),
        ("diferenciacion", "Diferenciacion", "Explica por que es distinto."),
    ),
    "idea_central": (
        ("medir_consumo", "Medir el consumo", "Sustituir la estimacion por una medicion verificable."),
        ("menos_es_mas", "Menos es mas", "Resolver con menos producto o menos pasos."),
        ("origen_natural", "Origen natural", "Explicar el resultado desde el origen o ingrediente."),
    ),
    "concepto": tuple(
        (key, label, _CONCEPT_DEFINITIONS.get(key, label))
        for key, label in CATALOG_CONCEPTS.items()
    ),
    "formato": (
        ("producto_resena", "Producto + resena", "Producto presentado junto a una resena."),
        ("pregunta_respuesta", "Pregunta + respuesta", "Abre con pregunta y responde."),
        ("editorial", "Editorial", "Pieza con tratamiento de contenido editorial."),
        ("tarjeta_testimonio", "Tarjeta de testimonio", "Testimonio en formato de tarjeta."),
        ("grid", "Grid", "Cuadricula de variantes o elementos."),
    ),
    "estilo": (
        ("ugc", "UGC", "Aspecto de contenido generado por usuario."),
        ("estudio", "Estudio", "Produccion controlada de estudio."),
        ("editorial", "Editorial", "Tratamiento editorial."),
        ("minimalista", "Minimalista", "Pocos elementos y jerarquia simple."),
        ("collage", "Collage", "Composicion por recortes o piezas."),
        ("handmade", "Handmade", "Recurso manual o dibujado."),
        ("captura_app", "Captura de app", "Captura de pantalla o interfaz."),
    ),
    "composicion": (
        ("producto_derecha", "Producto a la derecha", "Producto ubicado a la derecha."),
        ("headline_superior", "Headline superior", "Titular en la parte superior."),
        ("split_screen", "Split screen", "Pantalla dividida."),
        ("primer_plano", "Primer plano", "Encuadre cercano del sujeto."),
    ),
    "hook": (
        ("pregunta", "Pregunta", "Abre con una pregunta."),
        ("problema_explicito", "Problema explicito", "Nombra el problema de entrada."),
        ("cifra", "Cifra", "Abre con un numero o dato."),
        ("afirmacion", "Afirmacion", "Abre con una afirmacion fuerte."),
        ("curiosidad", "Curiosidad", "Abre un gap de curiosidad."),
    ),
    "mecanismo": (
        ("demostracion", "Demostracion", "Muestra el funcionamiento."),
        ("explicacion", "Explicacion", "Explica como funciona."),
        ("proceso", "Proceso", "Describe pasos o etapas."),
        ("caracteristica_verificable", "Caracteristica verificable", "Se apoya en una caracteristica comprobable."),
    ),
    "tipo_prueba": (
        ("especificacion_documentada", "Especificacion documentada", "Documento o ficha verificable."),
        ("demostracion_real", "Demostracion real", "Uso o resultado mostrado."),
        ("estudio_valido", "Estudio valido", "Estudio con metodologia verificable."),
        ("resena_verificada", "Resena verificada", "Resena con contexto o permiso."),
    ),
    "objecion": (
        ("compatibilidad", "Compatibilidad", "Funciona con lo que ya tiene."),
        ("instalacion", "Instalacion", "Es facil de instalar."),
        ("precio", "Precio", "Vale lo que cuesta."),
        ("garantia", "Garantia", "Hay respaldo o devolucion."),
        ("complejidad", "Complejidad", "No es dificil de usar."),
    ),
    "oferta": (
        ("descuento", "Descuento", "Precio reducido."),
        ("bundle", "Bundle", "Paquete de unidades o productos."),
        ("regalo", "Regalo", "Accesorio o producto adicional."),
        ("envio", "Envio", "Condicion de envio."),
        ("pago_contra_entrega", "Pago contra entrega", "Pago al recibir."),
    ),
    "cta": (
        ("comprar", "Comprar", "Solicita compra."),
        ("comparar", "Comparar", "Invita a comparar."),
        ("consultar", "Consultar", "Invita a preguntar."),
        ("aprender_mas", "Aprender mas", "Invita a obtener informacion."),
    ),
    "contexto_embudo": (
        ("descubrimiento", "Descubrimiento", "TOFU; presenta problema o categoria."),
        ("consideracion", "Consideracion", "MOFU; compara o explica."),
        ("conversion", "Conversion", "BOFU; ofrece y solicita accion."),
        ("retencion", "Retencion", "Post-compra o recompra."),
    ),
    "riesgo_cumplimiento": (
        ("salud", "Salud", "Afirmaciones de salud o cuerpo."),
        ("testimonios", "Testimonios", "Testimonios o resultados personales."),
        ("escasez_falsa", "Escasez falsa", "Urgencia o escasez no verificable."),
        ("antes_despues", "Antes / despues", "Comparacion visual de estados."),
        ("claims_absolutos", "Claims absolutos", "Promesas absolutas o garantizadas."),
    ),
    "idioma": (
        ("es", "Espanol", "Contenido en espanol."),
        ("en", "Ingles", "Contenido en ingles."),
    ),
    "mercado": (
        ("GT", "Guatemala", "Mercado de Guatemala."),
    ),
}

LEGACY_MAPPINGS: dict[tuple[str, str], tuple[str, str, str]] = {
    ("legacy_concepto_crudo", "C1_OFERTA"): ("concepto", "C1_OFERTA", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C2_BENEFICIOS"): ("concepto", "C2_BENEFICIOS", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C3_SINTOMA"): ("concepto", "C3_SINTOMA", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C4_TRANSFORMACION"): ("concepto", "C4_TRANSFORMACION", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C5_EVIDENCIA"): ("concepto", "C5_PRUEBA", "Evidencia es el nombre operativo previo de Prueba."),
    ("legacy_concepto_crudo", "C5_PRUEBA"): ("concepto", "C5_PRUEBA", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C6_UNBOXING"): ("concepto", "C5_PRUEBA", "C6 esta retirado; el catalogo lo define como variante de C5."),
    ("legacy_concepto_crudo", "C7_DESEO"): ("concepto", "C7_DESEO", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C8_PROGRESION"): ("concepto", "C8_PROGRESION", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C9_COMPARACION"): ("concepto", "C9_COMPARACION", "Coincidencia exacta con el catalogo canonico."),
    ("legacy_concepto_crudo", "C11_FORMULA"): ("concepto", "C2_BENEFICIOS", "El catalogo absorbe la ficha de formula en C2."),
    ("legacy_concepto_crudo", "C12_TESTIMONIO"): ("concepto", "C5_PRUEBA", "El catalogo incluye testimonios en C5."),
    ("legacy_concepto_crudo", "C13_AMENAZA"): ("concepto", "C4_TRANSFORMACION", "El catalogo absorbe la amenaza de progresion en C4."),
    ("legacy_gallery_auto", "OFERTA_PRECIO"): ("concepto", "C1_OFERTA", "Oferta y precio corresponden a C1."),
    ("legacy_gallery_auto", "TESTIMONIO"): ("concepto", "C5_PRUEBA", "El catalogo incluye testimonios en C5."),
    ("legacy_gallery_auto", "DEMO_USO"): ("concepto", "C5_PRUEBA", "El catalogo incluye demostraciones en C5."),
    ("legacy_gallery_auto", "PRUEBA_SOCIAL_NUM"): ("concepto", "C5_PRUEBA", "La prueba social numerica es evidencia de C5."),
    ("legacy_preclasificacion", "OFERTA_PRECIO"): ("concepto", "C1_OFERTA", "Oferta y precio corresponden a C1."),
    ("legacy_preclasificacion", "TESTIMONIO"): ("concepto", "C5_PRUEBA", "El catalogo incluye testimonios en C5."),
    ("legacy_preclasificacion", "DEMO_USO"): ("concepto", "C5_PRUEBA", "El catalogo incluye demostraciones en C5."),
    ("legacy_preclasificacion", "PRUEBA_SOCIAL_NUM"): ("concepto", "C5_PRUEBA", "La prueba social numerica es evidencia de C5."),
}

LEGACY_AMBIGUOUS = {
    ("legacy_concepto_crudo", "C10_INSTRUCTIVO"): "Puede ser educativo, beneficios o progresion; no hay equivalencia inequivoca.",
    ("legacy_gallery_auto", "AMENAZA_CHOQUE"): "La amenaza puede ser sintoma o transformacion; requiere revision.",
    ("legacy_gallery_auto", "EDUCATIVO_MECANISMO"): "Puede ser beneficios o progresion; requiere revision.",
    ("legacy_gallery_auto", "REVISAR_VISUAL"): "Etiqueta de triage visual, no un concepto canonico.",
    ("legacy_preclasificacion", "AMBIGUO"): "La propia etiqueta declara ambiguedad.",
    ("legacy_preclasificacion", "AMENAZA_CHOQUE"): "La amenaza puede ser sintoma o transformacion; requiere revision.",
    ("legacy_preclasificacion", "AUTORIDAD"): "El catalogo la trata como variante de C2, pero no es equivalencia directa.",
    ("legacy_preclasificacion", "CATALOGO_DINAMICO"): "Puede ser oferta, beneficios o formato; requiere revision.",
    ("legacy_preclasificacion", "EDUCATIVO_MECANISMO"): "Puede ser beneficios o progresion; requiere revision.",
    ("legacy_preclasificacion", "REVISAR_VISUAL"): "Etiqueta de triage visual, no un concepto canonico.",
}


def taxonomy_payload() -> dict[str, Any]:
    return {
        "version": TAXONOMY_VERSION,
        "source": TAXONOMY_SOURCE,
        "dimensions": [
            {
                "dimension": item["dimension"],
                "label": item["label"],
                "definition": item["definition"],
                "blueprint_section": item["blueprint_section"],
                "primary_required": item["primary_required"],
            }
            for item in DIMENSIONS
        ],
        "tags": {
            dimension: [
                {"tag_key": key, "label": label, "definition": definition}
                for key, label, definition in tags
            ]
            for dimension, tags in DIMENSION_TAGS.items()
        },
    }


def validate_definitions() -> None:
    dimensions = {item["dimension"] for item in DIMENSIONS}
    if len(dimensions) != len(DIMENSIONS):
        raise ValueError("Duplicate taxonomy dimension")
    missing = dimensions - set(DIMENSION_TAGS)
    if missing:
        raise ValueError(f"Dimensions without tags: {sorted(missing)}")
    extra = set(DIMENSION_TAGS) - dimensions
    if extra:
        raise ValueError(f"Tags for unknown dimensions: {sorted(extra)}")
    for dimension, tags in DIMENSION_TAGS.items():
        keys = [key for key, _, _ in tags]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate tags in {dimension}")
        if not keys:
            raise ValueError(f"Dimension {dimension} has no tags")
        for key, label, definition in tags:
            if not key.strip() or not label.strip() or not definition.strip():
                raise ValueError(f"Incomplete tag definition: {dimension}:{key}")
    if "C6_UNBOXING" in CANONICAL_CONCEPT_KEYS or any(
        key.startswith("C6") for key in CANONICAL_CONCEPT_KEYS
    ):
        raise ValueError("C6 must not be canonical")
    if "C6_UNBOXING" in {key for key, _, _ in DIMENSION_TAGS["concepto"]}:
        raise ValueError("C6 must not be seeded as a canonical concept")


def seed_taxonomy(connection: sqlite3.Connection, root: Path | None = None) -> dict[str, Any]:
    validate_definitions()
    now = utc_now()
    definition = canonical_json(taxonomy_payload())
    source_hash = None
    if root is not None:
        blueprint = root / "Blueprint_Maestro_Inteligencia_Creativa_Ads_v1.md"
        if blueprint.is_file():
            source_hash = sha256_file(blueprint)
    connection.execute(
        """
        INSERT OR IGNORE INTO taxonomy_version
            (version, status, source, source_hash, definition_json, created_at, activated_at)
        VALUES (?, 'active', ?, ?, ?, ?, ?)
        """,
        (TAXONOMY_VERSION, TAXONOMY_SOURCE, source_hash, definition, now, now),
    )
    connection.execute(
        """
        UPDATE taxonomy_version
        SET source_hash = COALESCE(source_hash, ?),
            definition_json = CASE
                WHEN definition_json IS NULL OR TRIM(definition_json) = '' OR definition_json = '{}'
                THEN ?
                ELSE definition_json
            END
        WHERE version = ?
        """,
        (source_hash, definition, TAXONOMY_VERSION),
    )
    for item in DIMENSIONS:
        connection.execute(
            """
            INSERT OR IGNORE INTO taxonomy_dimension
                (taxonomy_version, dimension, label, definition, blueprint_section,
                 allows_multiple, primary_required, sort_order, active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, 1, ?)
            """,
            (
                TAXONOMY_VERSION,
                item["dimension"],
                item["label"],
                item["definition"],
                item["blueprint_section"],
                1 if item["primary_required"] else 0,
                item["sort_order"],
                now,
            ),
        )
    tag_count = 0
    for dimension, tags in DIMENSION_TAGS.items():
        for key, label, tag_definition in tags:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO tag_definition
                    (dimension, tag_key, label, definition, version, active, source,
                     created_at, taxonomy_version)
                VALUES (?, ?, ?, ?, 1, 1, ?, ?, ?)
                """,
                (
                    dimension,
                    key,
                    label,
                    tag_definition,
                    TAXONOMY_SOURCE,
                    now,
                    TAXONOMY_VERSION,
                ),
            )
            if cursor.rowcount:
                tag_count += 1
    return {
        "version": TAXONOMY_VERSION,
        "dimensions": len(DIMENSIONS),
        "tags_inserted": tag_count,
        "source_hash": source_hash,
        "definition_hash": sha256_text(definition),
    }


def list_taxonomy(
    connection: sqlite3.Connection,
    *,
    version: str = TAXONOMY_VERSION,
    dimension: str | None = None,
) -> list[dict[str, Any]]:
    clauses = ["taxonomy_version = ?"]
    parameters: list[Any] = [version]
    if dimension:
        clauses.append("dimension = ?")
        parameters.append(dimension)
    dimensions = [
        dict(row)
        for row in connection.execute(
            f"""
            SELECT taxonomy_version, dimension, label, definition, blueprint_section,
                   allows_multiple, primary_required, sort_order, active
            FROM taxonomy_dimension
            WHERE {' AND '.join(clauses)}
            ORDER BY sort_order, dimension
            """,
            parameters,
        )
    ]
    for item in dimensions:
        item["tags"] = [
            dict(row)
            for row in connection.execute(
                """
                SELECT tag_key, label, definition, version, active, source
                FROM tag_definition
                WHERE dimension = ? AND taxonomy_version = ? AND active = 1
                ORDER BY tag_key
                """,
                (item["dimension"], version),
            )
        ]
    return dimensions


def backfill_primary_concepts(connection: sqlite3.Connection) -> int:
    cursor = connection.execute(
        """
        UPDATE ad_tag
        SET is_primary = 1
        WHERE id IN (
            SELECT MIN(t.id)
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension = 'concepto'
              AND t.review_status IN ('reviewed', 'approved')
            GROUP BY t.ad_creative_id
        )
          AND is_primary = 0
          AND NOT EXISTS (
              SELECT 1 FROM ad_tag p
              WHERE p.ad_creative_id = ad_tag.ad_creative_id
                AND p.is_primary = 1
          )
        """
    )
    return int(cursor.rowcount)


def canonical_tag_map(connection: sqlite3.Connection) -> dict[str, dict[str, int]]:
    rows = connection.execute(
        """
        SELECT dimension, tag_key, id
        FROM tag_definition
        WHERE taxonomy_version = ? AND active = 1
          AND dimension IN ({placeholders})
        ORDER BY dimension, tag_key
        """.format(placeholders=", ".join("?" for _ in CANONICAL_DIMENSIONS)),
        (TAXONOMY_VERSION, *CANONICAL_DIMENSIONS),
    ).fetchall()
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        result.setdefault(row["dimension"], {})[row["tag_key"]] = int(row["id"])
    return result


def tag_definition_id(
    connection: sqlite3.Connection,
    dimension: str,
    tag_key: str,
    *,
    version: str = TAXONOMY_VERSION,
) -> int | None:
    row = connection.execute(
        """
        SELECT id
        FROM tag_definition
        WHERE dimension = ? AND tag_key = ? AND taxonomy_version = ? AND active = 1
        ORDER BY version DESC
        LIMIT 1
        """,
        (dimension, tag_key, version),
    ).fetchone()
    return int(row["id"]) if row is not None else None


def validate_tag(
    connection: sqlite3.Connection,
    dimension: str,
    tag_key: str,
    *,
    version: str = TAXONOMY_VERSION,
) -> int:
    if dimension not in CANONICAL_DIMENSIONS:
        raise ValueError(f"Unknown canonical dimension: {dimension}")
    if dimension == "concepto" and tag_key.startswith("C6"):
        raise ValueError("C6 is retired and cannot be assigned as a canonical concept")
    definition_id = tag_definition_id(connection, dimension, tag_key, version=version)
    if definition_id is None:
        raise ValueError(f"Unknown canonical tag: {dimension}:{tag_key} ({version})")
    return definition_id
