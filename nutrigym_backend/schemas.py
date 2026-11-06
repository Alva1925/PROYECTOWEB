# ============================================================
# schemas.py
# Esquemas Pydantic para validación de entrada/salida de datos.
# Patrón usado: XBase (campos comunes) → XCreate (entrada) →
#               XOut (salida con id y campos calculados).
# ============================================================

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────
# USUARIO
# ──────────────────────────────────────────────────────────

class UsuarioBase(BaseModel):
    nombre:        str
    peso_actual:   float = Field(..., gt=0, description="Peso en kg, debe ser mayor a 0")
    meta_calorias: int   = Field(default=2000, ge=500)
    meta_proteina: int   = Field(default=150,  ge=10)


class UsuarioCreate(UsuarioBase):
    """Payload para POST /usuarios/"""
    pass


class UsuarioOut(UsuarioBase):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2 (era orm_mode en v1)


# ──────────────────────────────────────────────────────────
# EJERCICIO
# ──────────────────────────────────────────────────────────

class EjercicioBase(BaseModel):
    nombre:         str
    grupo_muscular: str


class EjercicioCreate(EjercicioBase):
    """Payload para POST /ejercicios/"""
    pass


class EjercicioOut(EjercicioBase):
    id: int

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────
# EJERCICIO RUTINA  (tabla pivote)
# ──────────────────────────────────────────────────────────

class EjercicioRutinaBase(BaseModel):
    ejercicio_id:   int
    series:         int   = Field(default=3,   ge=1)
    repeticiones:   int   = Field(default=10,  ge=1)
    peso_soportado: float = Field(default=0.0, ge=0)


class EjercicioRutinaCreate(EjercicioRutinaBase):
    """Detalle de ejercicio dentro del payload de creación de rutina."""
    pass


class EjercicioRutinaOut(EjercicioRutinaBase):
    id:       int
    ejercicio: Optional[EjercicioOut] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────
# RUTINA
# ──────────────────────────────────────────────────────────

class RutinaBase(BaseModel):
    nombre:     str
    usuario_id: int


class RutinaCreate(RutinaBase):
    """Payload para POST /rutinas/ — incluye la lista de ejercicios."""
    ejercicios: List[EjercicioRutinaCreate] = Field(default_factory=list)


class RutinaOut(RutinaBase):
    id:        int
    ejercicios: List[EjercicioRutinaOut] = Field(default_factory=list, alias="ejercicio_rutinas")

    class Config:
        from_attributes = True
        populate_by_name = True   # permite usar tanto el alias como el nombre real


# ──────────────────────────────────────────────────────────
# ALIMENTO
# ──────────────────────────────────────────────────────────

class AlimentoBase(BaseModel):
    nombre:              str
    calorias_por_racion: int   = Field(default=0, ge=0)
    proteina_por_racion: float = Field(default=0.0, ge=0)


class AlimentoCreate(AlimentoBase):
    """Payload para POST /alimentos/"""
    pass


class AlimentoOut(AlimentoBase):
    id: int

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────
# REGISTRO ALIMENTO  (línea de detalle)
# ──────────────────────────────────────────────────────────

class RegistroAlimentoBase(BaseModel):
    alimento_id: int
    porciones:   float = Field(default=1.0, gt=0)


class RegistroAlimentoCreate(RegistroAlimentoBase):
    """Payload para agregar un alimento al registro diario."""
    pass


class RegistroAlimentoOut(RegistroAlimentoBase):
    id:      int
    alimento: Optional[AlimentoOut] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────
# REGISTRO DIARIO
# ──────────────────────────────────────────────────────────

class RegistroDiarioBase(BaseModel):
    usuario_id:     int
    fecha:          date
    total_calorias: int   = 0
    total_proteinas: float = 0.0


class RegistroDiarioOut(RegistroDiarioBase):
    id:                int
    registros_alimento: List[RegistroAlimentoOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────
# RESPUESTA DEL AGENTE
# ──────────────────────────────────────────────────────────

class AgenteResponse(BaseModel):
    """Respuesta estructurada del motor agéntico."""
    usuario:         str
    fecha:           date
    total_calorias:  int
    meta_calorias:   int
    total_proteinas: float
    meta_proteina:   int
    estado_calorias: str   # "déficit" | "exceso" | "óptimo"
    estado_proteina: str   # "déficit" | "exceso" | "óptimo"
    retroalimentacion: str # Mensaje en lenguaje natural (ODS 3)
