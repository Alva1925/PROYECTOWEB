# ============================================================
# main.py
# Aplicación FastAPI de NutriGym Agent.
# Expone los endpoints REST y orquesta la lógica de negocio.
# ============================================================

from datetime import date
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Importaciones internas del paquete nutrigym_backend
from .database import engine, Base, get_db
from . import models, schemas
from .agent import evaluar_registro_diario_agente

# ─── Creación automática de tablas al iniciar ──────────────────────────────
# Esto garantiza que la BD esté lista sin migraciones manuales en el MVP.
Base.metadata.create_all(bind=engine)

# ─── Instancia de la aplicación ───────────────────────────────────────────
app = FastAPI(
    title="NutriGym Agent API",
    description=(
        "Backend del sistema NutriGym Agent — Hackathon ODS 3: Salud y Bienestar. "
        "Gestiona usuarios, rutinas de entrenamiento, registro nutricional diario "
        "y genera retroalimentación agéntica personalizada."
    ),
    version="1.0.0",
)


# ===========================================================================
# USUARIOS
# ===========================================================================

@app.post(
    "/usuarios/",
    response_model=schemas.UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
    summary="Crear un nuevo usuario",
)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un atleta con su perfil y metas nutricionales."""
    db_usuario = models.Usuario(**usuario.model_dump())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


@app.get(
    "/usuarios/{usuario_id}",
    response_model=schemas.UsuarioOut,
    tags=["Usuarios"],
    summary="Obtener perfil y metas de un usuario",
)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Devuelve el perfil completo y las metas nutricionales del usuario."""
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


# ===========================================================================
# ENTRENAMIENTO — Ejercicios
# ===========================================================================

@app.post(
    "/ejercicios/",
    response_model=schemas.EjercicioOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Entrenamiento"],
    summary="Agregar ejercicio al catálogo",
)
def crear_ejercicio(ejercicio: schemas.EjercicioCreate, db: Session = Depends(get_db)):
    """Crea un ejercicio en el catálogo maestro reutilizable en cualquier rutina."""
    db_ejercicio = models.Ejercicio(**ejercicio.model_dump())
    db.add(db_ejercicio)
    db.commit()
    db.refresh(db_ejercicio)
    return db_ejercicio


# ===========================================================================
# ENTRENAMIENTO — Rutinas
# ===========================================================================

@app.post(
    "/rutinas/",
    response_model=schemas.RutinaOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Entrenamiento"],
    summary="Crear una rutina de entrenamiento",
)
def crear_rutina(rutina: schemas.RutinaCreate, db: Session = Depends(get_db)):
    """
    Crea una rutina y asocia los ejercicios indicados con sus
    series, repeticiones y peso soportado.
    """
    # Verificar que el usuario existe
    usuario = db.query(models.Usuario).filter(models.Usuario.id == rutina.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Crear la rutina base
    db_rutina = models.Rutina(nombre=rutina.nombre, usuario_id=rutina.usuario_id)
    db.add(db_rutina)
    db.flush()  # Obtenemos el id de la rutina sin hacer commit todavía

    # Crear las filas de la tabla pivote EjercicioRutina
    for item in rutina.ejercicios:
        # Verificar que cada ejercicio del payload existe en el catálogo
        ejercicio = db.query(models.Ejercicio).filter(
            models.Ejercicio.id == item.ejercicio_id
        ).first()
        if not ejercicio:
            db.rollback()
            raise HTTPException(
                status_code=404,
                detail=f"Ejercicio con id={item.ejercicio_id} no encontrado en el catálogo",
            )
        db_er = models.EjercicioRutina(
            rutina_id=db_rutina.id,
            **item.model_dump(),
        )
        db.add(db_er)

    db.commit()
    db.refresh(db_rutina)
    return db_rutina


@app.get(
    "/rutinas/usuario/{usuario_id}",
    response_model=List[schemas.RutinaOut],
    tags=["Entrenamiento"],
    summary="Obtener rutinas de un usuario",
)
def obtener_rutinas_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Lista todas las rutinas de entrenamiento del usuario con sus ejercicios."""
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario.rutinas


# ===========================================================================
# NUTRICIÓN — Alimentos
# ===========================================================================

@app.post(
    "/alimentos/",
    response_model=schemas.AlimentoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Nutrición"],
    summary="Agregar alimento al catálogo",
)
def crear_alimento(alimento: schemas.AlimentoCreate, db: Session = Depends(get_db)):
    """Crea un alimento en el catálogo maestro con su información nutricional por ración."""
    db_alimento = models.Alimento(**alimento.model_dump())
    db.add(db_alimento)
    db.commit()
    db.refresh(db_alimento)
    return db_alimento


# ===========================================================================
# NUTRICIÓN — Registro Diario
# ===========================================================================

@app.post(
    "/registros-diarios/{usuario_id}/agregar-alimento",
    response_model=schemas.RegistroDiarioOut,
    status_code=status.HTTP_200_OK,
    tags=["Nutrición"],
    summary="Registrar consumo de un alimento en el día actual",
)
def agregar_alimento_registro(
    usuario_id: int,
    payload: schemas.RegistroAlimentoCreate,
    db: Session = Depends(get_db),
):
    """
    Agrega un alimento (con porciones) al RegistroDiario de hoy.
    Si el registro del día no existe, lo crea automáticamente.
    Recalcula total_calorias y total_proteinas en cada llamada.
    """
    # 1. Verificar usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2. Verificar alimento
    alimento = db.query(models.Alimento).filter(models.Alimento.id == payload.alimento_id).first()
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado en el catálogo")

    hoy = date.today()

    # 3. Obtener o crear el RegistroDiario del día
    registro = db.query(models.RegistroDiario).filter(
        models.RegistroDiario.usuario_id == usuario_id,
        models.RegistroDiario.fecha == hoy,
    ).first()

    if not registro:
        registro = models.RegistroDiario(usuario_id=usuario_id, fecha=hoy)
        db.add(registro)
        db.flush()

    # 4. Crear la línea de detalle RegistroAlimento
    registro_alimento = models.RegistroAlimento(
        registro_diario_id=registro.id,
        alimento_id=payload.alimento_id,
        porciones=payload.porciones,
    )
    db.add(registro_alimento)

    # 5. Recalcular totales acumulados considerando las porciones consumidas
    registro.total_calorias  += int(alimento.calorias_por_racion * payload.porciones)
    registro.total_proteinas += alimento.proteina_por_racion * payload.porciones

    db.commit()
    db.refresh(registro)
    return registro


# ===========================================================================
# ANÁLISIS AGÉNTICO
# ===========================================================================

@app.get(
    "/registros-diarios/{usuario_id}/analisis-agente",
    response_model=schemas.AgenteResponse,
    tags=["Agente"],
    summary="Obtener retroalimentación agéntica del día actual",
)
def analisis_agente(usuario_id: int, db: Session = Depends(get_db)):
    """
    Ejecuta el motor agéntico sobre el RegistroDiario del día actual y
    devuelve retroalimentación personalizada alineada al ODS 3.
    Si no hay registro para hoy, devuelve el análisis con valores en cero
    para motivar al usuario a comenzar su registro.
    """
    # 1. Verificar usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    hoy = date.today()

    # 2. Buscar el registro diario de hoy; si no existe, crear uno vacío en memoria
    #    (no se persiste, solo sirve para la evaluación agéntica)
    registro = db.query(models.RegistroDiario).filter(
        models.RegistroDiario.usuario_id == usuario_id,
        models.RegistroDiario.fecha == hoy,
    ).first()

    if not registro:
        # Registro sintético para que el agente pueda evaluar y motivar al usuario
        registro = models.RegistroDiario(
            usuario_id=usuario_id,
            fecha=hoy,
            total_calorias=0,
            total_proteinas=0.0,
        )

    # 3. Invocar el motor agéntico y devolver la respuesta
    resultado = evaluar_registro_diario_agente(usuario, registro)
    return resultado
