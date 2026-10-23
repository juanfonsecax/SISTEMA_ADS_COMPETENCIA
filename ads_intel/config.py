from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent

DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "ads_intel.db"
DEFAULT_MANIFEST_PATH = DATA_DIR / "manifests" / "legacy_manifest.json"
DEFAULT_BACKUP_DIR = DATA_DIR / "backups"
DEFAULT_THUMBNAIL_DIR = DATA_DIR / "visual_thumbnails"

SOURCE_NAME = "meta_ad_library_gt_legacy"
SOURCE_TYPE = "manual_browser_export"
SOURCE_PERMISSION_BASIS = "pending_review"

AD_FILES = ("_ADS.csv", "_BANCO.csv")

LEGACY_RAW_GLOBS = ("_RAW/**/*",)

LEGACY_BACKUP_GLOBS = (
    "*.py",
    "*.js",
    "*.md",
    "*.txt",
    "*.csv",
    "*.html",
    "_BLUEPRINTS/**/*.py",
    "_BLUEPRINTS/**/*.js",
    "_BLUEPRINTS/**/*.json",
    "_BLUEPRINTS/**/*.md",
    "_BLUEPRINTS/**/*.txt",
    "_BLUEPRINTS/**/*.html",
    "_BANCO_CREATIVOS/**/*.csv",
    "_BANCO_CREATIVOS/**/*.md",
    "_BANCO_CREATIVOS/**/*.jpg",
    "ANALISIS/**/*.md",
    "tests/**/*.py",
    "odd/**/*.md",
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

