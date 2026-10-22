from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent

DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "ads_intel.db"
DEFAULT_MANIFEST_PATH = DATA_DIR / "manifests" / "legacy_manifest.json"
DEFAULT_BACKUP_DIR = DATA_DIR / "backups"

SOURCE_NAME = "meta_ad_library_gt_legacy"
SOURCE_TYPE = "manual_browser_export"
SOURCE_PERMISSION_BASIS = "pending_review"

AD_FILES = ("_ADS.csv", "_BANCO.csv")

LEGACY_INPUT_FILES = (
    "_ADS.csv",
    "_BANCO.csv",
    "_PAGINAS.csv",
    "_RANKING_CUENTAS.csv",
    "_SELECCION_EXTRACCION.csv",
    "_ELEMENTOS.csv",
    "_CLASIF_FAVORITOS.csv",
    "_ETIQUETAS_MANUALES.csv",
    "_PRECLASIFICACION.csv",
    "_COPIES.csv",
    "_BANCO_CREATIVOS/_INDICE.csv",
    "_BLUEPRINTS/FICHAS/_MANIFIESTO.csv",
    "_CATALOGO_CONCEPTOS.md",
    "_ESTRATEGIA_CONCEPTOS.md",
    "_METODO.md",
    "analisis-ad-2026-08-18.md",
    "README.md",
    "_HANDOFF.md",
    "_HANDOFF_CONCEPTOS.md",
    "_PROCESADOS.txt",
    "_PENDIENTES.txt",
    "_VISTAS.txt",
    "_LINKS_TANDAS.txt",
    "_BLUEPRINTS/_LEEME.md",
    "_BLUEPRINTS/_ESQUEMA_FICHA.md",
    "_BLUEPRINTS/_PROMPT_LLENADOR.txt",
    "_BLUEPRINTS/_PROMPT_RENDER.txt",
    "_BLUEPRINTS/ficha_tinnidrop.json",
    "_BANCO_CREATIVOS/_LEEME.md",
    "gen_galeria.py",
    "gen_winners.py",
    "clasificar_conceptos.py",
    "_codificar.py",
    "integrar_copies.py",
    "bajar.py",
    "bajar2.py",
    "dedup.py",
    "_EXTRACTOR.js",
)

LEGACY_JSON_GLOBS = (
    "_BLUEPRINTS/FICHAS/F*.json",
    "_BLUEPRINTS/CANONICOS/*.json",
    "_BLUEPRINTS/blueprint_*.json",
    "_BLUEPRINTS/LLENO_T01_*.json",
)

LEGACY_RAW_GLOBS = ("_RAW/**/*",)

LEGACY_BACKUP_GLOBS = (
    "*.py",
    "*.js",
    "*.md",
    "*.txt",
    "*.csv",
    "_BLUEPRINTS/**/*.json",
    "_BLUEPRINTS/**/*.md",
    "_BLUEPRINTS/**/*.txt",
    "_BANCO_CREATIVOS/**/*.csv",
    "_BANCO_CREATIVOS/**/*.md",
    "ANALISIS/**/*.md",
)

CATALOG_CONCEPTS = {
    "C1_OFERTA": "Oferta",
    "C2_BENEFICIOS": "Beneficios",
    "C3_SINTOMA": "Sintoma",
    "C4_TRANSFORMACION": "Transformacion",
    "C5_PRUEBA": "Prueba",
    "C7_DESEO": "Deseo",
    "C8_PROGRESION": "Progresion",
    "C9_COMPARACION": "Comparacion",
    "SIN_CLASIFICAR": "Sin clasificar",
}

GALLERY_CONCEPTS = (
    "TESTIMONIO",
    "DEMO_USO",
    "EDUCATIVO",
    "COMPARACION",
    "AUTORIDAD",
    "PRUEBA_SOCIAL",
    "OFERTA_PRECIO",
    "AMENAZA",
    "PRODUCTO_HERO",
    "CHAT",
    "UGC_NATIVO",
)

PRECLASSIFICATION_CONCEPTS = (
    "REVISAR_VISUAL",
    "OFERTA_PRECIO",
    "CATALOGO_DINAMICO",
    "AUTORIDAD",
    "PRUEBA_SOCIAL_NUM",
    "TESTIMONIO",
    "AMENAZA_CHOQUE",
    "EDUCATIVO_MECANISMO",
    "AMBIGUO",
    "DEMO_USO",
)

TAG_DIMENSIONS = {
    "concepto": "Catalogo canonico de conceptos creativos",
    "legacy_concepto_crudo": "Etiquetas crudas del operador",
    "legacy_gallery_auto": "Vocabulario antiguo de la galeria",
    "legacy_preclasificacion": "Etiquetas automaticas por reglas de texto",
    "curaduria": "Seleccion manual del operador",
}

