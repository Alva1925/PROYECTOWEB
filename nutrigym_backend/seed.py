# ============================================================
# seed.py
# Precarga de datos demo para el Hackathon.
#
# La función ejecutar_seed() se llama al arrancar el servidor
# y comprueba si ya existen datos antes de insertar nada,
# por lo que es completamente idempotente: ejecutarla varias
# veces no genera duplicados.
# ============================================================

from .database import SessionLocal
from . import models


# ---------------------------------------------------------------------------
# Datos de demo
# ---------------------------------------------------------------------------

_EJERCICIOS = [
    {"nombre": "Press de Banca",  "grupo_muscular": "Pecho"},
    {"nombre": "Sentadilla",      "grupo_muscular": "Piernas"},
    {"nombre": "Peso Muerto",     "grupo_muscular": "Espalda / Glúteos"},
    {"nombre": "Dominadas",       "grupo_muscular": "Espalda / Bíceps"},
    {"nombre": "Press Militar",   "grupo_muscular": "Hombros"},
]

# Valores nutricionales por ración estándar (100 g o unidad indicada)
_ALIMENTOS = [
    {"nombre": "Pechuga de Pollo (100 g)", "calorias_por_racion": 165, "proteina_por_racion": 31.0},
    {"nombre": "Huevo entero (1 unidad)",  "calorias_por_racion": 78,  "proteina_por_racion": 6.3},
    {"nombre": "Arroz cocido (100 g)",     "calorias_por_racion": 130, "proteina_por_racion": 2.7},
    {"nombre": "Yogur Griego (100 g)",     "calorias_por_racion": 97,  "proteina_por_racion": 9.0},
    {"nombre": "Proteína Whey (1 scoop)",  "calorias_por_racion": 120, "proteina_por_racion": 25.0},
]

_USUARIO_DEMO = {
    "nombre":        "Atleta Demo",
    "peso_actual":   80.0,
    "meta_calorias": 2500,
    "meta_proteina": 160,
}


# ---------------------------------------------------------------------------
# Función principal — idempotente
# ---------------------------------------------------------------------------

def ejecutar_seed() -> None:
    """
    Precarga el usuario de prueba, ejercicios y alimentos si las tablas
    están vacías. No hace nada si ya existen datos.
    """
    db = SessionLocal()
    try:
        # ── Ejercicios ──────────────────────────────────────────────────
        if db.query(models.Ejercicio).count() == 0:
            db.add_all([models.Ejercicio(**e) for e in _EJERCICIOS])
            db.commit()

        # ── Alimentos ───────────────────────────────────────────────────
        if db.query(models.Alimento).count() == 0:
            db.add_all([models.Alimento(**a) for a in _ALIMENTOS])
            db.commit()

        # ── Usuario demo ────────────────────────────────────────────────
        if db.query(models.Usuario).count() == 0:
            db.add(models.Usuario(**_USUARIO_DEMO))
            db.commit()

    finally:
        db.close()
