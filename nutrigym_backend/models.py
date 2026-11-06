# ============================================================
# models.py
# Definición de las tablas ORM con SQLAlchemy.
# Representa el dominio de NutriGym: usuarios, ejercicios,
# rutinas, alimentos y registros diarios.
# ============================================================

from datetime import date
from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .database import Base


# ------------------------------------------------------------------
# 1. Usuario
#    Entidad central del sistema. Almacena el perfil del atleta y
#    sus metas nutricionales que el agente usará para evaluar el día.
# ------------------------------------------------------------------
class Usuario(Base):
    __tablename__ = "usuarios"

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre         = Column(String, nullable=False)
    peso_actual    = Column(Float, nullable=False)
    meta_calorias  = Column(Integer, default=2000)   # kcal/día
    meta_proteina  = Column(Integer, default=150)    # gramos/día

    # Relaciones 1 → N
    rutinas          = relationship("Rutina",         back_populates="usuario", cascade="all, delete-orphan")
    registros_diarios = relationship("RegistroDiario", back_populates="usuario", cascade="all, delete-orphan")


# ------------------------------------------------------------------
# 2. Ejercicio
#    Catálogo maestro de ejercicios reutilizables en cualquier rutina.
# ------------------------------------------------------------------
class Ejercicio(Base):
    __tablename__ = "ejercicios"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre          = Column(String, nullable=False)
    grupo_muscular  = Column(String, nullable=False)

    # Relación inversa con la tabla pivote EjercicioRutina
    ejercicio_rutinas = relationship("EjercicioRutina", back_populates="ejercicio")


# ------------------------------------------------------------------
# 3. Rutina
#    Agrupa ejercicios bajo un plan de entrenamiento personalizado.
# ------------------------------------------------------------------
class Rutina(Base):
    __tablename__ = "rutinas"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre      = Column(String, nullable=False)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario           = relationship("Usuario",          back_populates="rutinas")
    ejercicio_rutinas = relationship("EjercicioRutina",  back_populates="rutina", cascade="all, delete-orphan")


# ------------------------------------------------------------------
# 4. EjercicioRutina  (tabla pivote / asociación)
#    Vincula un ejercicio concreto a una rutina especificando el
#    volumen de entrenamiento: series, repeticiones y peso levantado.
# ------------------------------------------------------------------
class EjercicioRutina(Base):
    __tablename__ = "ejercicio_rutina"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rutina_id       = Column(Integer, ForeignKey("rutinas.id"),    nullable=False)
    ejercicio_id    = Column(Integer, ForeignKey("ejercicios.id"), nullable=False)
    series          = Column(Integer, default=3)
    repeticiones    = Column(Integer, default=10)
    peso_soportado  = Column(Float,   default=0.0)   # kg

    rutina    = relationship("Rutina",    back_populates="ejercicio_rutinas")
    ejercicio = relationship("Ejercicio", back_populates="ejercicio_rutinas")


# ------------------------------------------------------------------
# 5. Alimento
#    Catálogo maestro de alimentos con información nutricional
#    por ración estándar.
# ------------------------------------------------------------------
class Alimento(Base):
    __tablename__ = "alimentos"

    id                   = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre               = Column(String, nullable=False)
    calorias_por_racion  = Column(Integer, default=0)   # kcal
    proteina_por_racion  = Column(Float,   default=0.0) # gramos

    registros_alimento = relationship("RegistroAlimento", back_populates="alimento")


# ------------------------------------------------------------------
# 6. RegistroDiario
#    Acumula el consumo nutricional de un usuario en una fecha dada.
#    El agente evalúa este registro para generar retroalimentación.
#    La restricción UniqueConstraint garantiza 1 registro por día
#    por usuario.
# ------------------------------------------------------------------
class RegistroDiario(Base):
    __tablename__ = "registros_diarios"

    id               = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id       = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha            = Column(Date, default=date.today)
    total_calorias   = Column(Integer, default=0)
    total_proteinas  = Column(Float,   default=0.0)

    __table_args__ = (
        UniqueConstraint("usuario_id", "fecha", name="uq_usuario_fecha"),
    )

    usuario            = relationship("Usuario",         back_populates="registros_diarios")
    registros_alimento = relationship("RegistroAlimento", back_populates="registro_diario", cascade="all, delete-orphan")


# ------------------------------------------------------------------
# 7. RegistroAlimento
#    Línea de detalle dentro de un RegistroDiario: qué alimento
#    se consumió y cuántas porciones.
# ------------------------------------------------------------------
class RegistroAlimento(Base):
    __tablename__ = "registro_alimentos"

    id                 = Column(Integer, primary_key=True, index=True, autoincrement=True)
    registro_diario_id = Column(Integer, ForeignKey("registros_diarios.id"), nullable=False)
    alimento_id        = Column(Integer, ForeignKey("alimentos.id"),         nullable=False)
    porciones          = Column(Float, default=1.0)

    registro_diario = relationship("RegistroDiario", back_populates="registros_alimento")
    alimento        = relationship("Alimento",       back_populates="registros_alimento")
