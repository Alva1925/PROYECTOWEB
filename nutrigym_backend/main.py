# ============================================================
# main.py
# Aplicación FastAPI de NutriGym Agent — versión Hackathon.
# Expone los endpoints REST y orquesta la lógica de negocio.
# ============================================================

from datetime import date
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from . import models, schemas
from .agent import evaluar_registro_diario_agente
from .seed import ejecutar_seed

# ─── Creación automática de tablas ────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── Precarga de datos demo (solo si las tablas están vacías) ─────────────
ejecutar_seed()

# ─── Metadatos de la API para Swagger UI ─────────────────────────────────
_DESCRIPTION = """
## NutriGym Agent API 🏋️‍♂️🥗

Backend del sistema **NutriGym Agent**, desarrollado para el
**Hackathon de Desarrollo Sustentable — ODS 3: Salud y Bienestar**.

### Módulos disponibles
| Módulo | Descripción |
|---|---|
| **Usuarios** | Registro de atletas y seguimiento de peso corporal |
| **Entrenamiento** | Catálogo de ejercicios y creación de rutinas personalizadas |
| **Nutrición** | Catálogo de alimentos y registro nutricional diario |
| **Agente** | Motor de análisis con retroalimentación personalizada (ODS 3) |

> Los datos de demo se precargan automáticamente al iniciar el servidor.
> Usuario de prueba: **id = 1**.
"""

app = FastAPI(
    title="NutriGym Agent API",
    description=_DESCRIPTION,
    version="1.0.0",
    contact={
        "name": "Equipo NutriGym — Hackathon ODS 3",
    },
    license_info={
        "name": "MIT",
    },
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
    response_description="Perfil del usuario creado con su id asignado",
)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registra un atleta con nombre, peso actual y metas nutricionales diarias.

    - **meta_calorias**: objetivo de ingesta calórica en kcal (default 2 000).
    - **meta_proteina**: objetivo de consumo proteico en gramos (default 150).
    """
    db_usuario = models.Usuario(**usuario.model_dump())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


@app.get(
    "/usuarios/{usuario_id}",
    response_model=schemas.UsuarioOut,
    status_code=status.HTTP_200_OK,
    tags=["Usuarios"],
    summary="Obtener perfil y metas de un usuario",
    response_description="Perfil completo del usuario",
)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Devuelve el perfil y las metas nutricionales del usuario indicado."""
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


@app.patch(
    "/usuarios/{usuario_id}/peso",
    response_model=schemas.UsuarioOut,
    status_code=status.HTTP_200_OK,
    tags=["Usuarios"],
    summary="Actualizar peso corporal del usuario",
    response_description="Perfil actualizado con el nuevo peso",
)
def actualizar_peso(
    usuario_id: int,
    payload: schemas.PesoUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza únicamente el campo `peso_actual` del usuario.

    Permite llevar un seguimiento de la evolución corporal a lo largo
    del tiempo, alineado al ODS 3 en el monitoreo de la salud física.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    usuario.peso_actual = payload.peso_actual
    db.commit()
    db.refresh(usuario)
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
    response_description="Ejercicio creado con su id asignado",
)
def crear_ejercicio(ejercicio: schemas.EjercicioCreate, db: Session = Depends(get_db)):
    """
    Crea un ejercicio en el catálogo maestro.
    Los ejercicios del catálogo son reutilizables en cualquier rutina de entrenamiento.
    """
    db_ejercicio = models.Ejercicio(**ejercicio.model_dump())
    db.add(db_ejercicio)
    db.commit()
    db.refresh(db_ejercicio)
    return db_ejercicio


@app.get(
    "/ejercicios/",
    response_model=List[schemas.EjercicioOut],
    status_code=status.HTTP_200_OK,
    tags=["Entrenamiento"],
    summary="Listar catálogo de ejercicios",
    response_description="Lista completa de ejercicios disponibles",
)
def listar_ejercicios(db: Session = Depends(get_db)):
    """
    Devuelve todos los ejercicios disponibles en el catálogo maestro,
    ordenados por nombre, con su grupo muscular asociado.
    """
    return db.query(models.Ejercicio).order_by(models.Ejercicio.nombre).all()


# ===========================================================================
# ENTRENAMIENTO — Rutinas
# ===========================================================================

@app.post(
    "/rutinas/",
    response_model=schemas.RutinaOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Entrenamiento"],
    summary="Crear una rutina de entrenamiento",
    response_description="Rutina creada con sus ejercicios vinculados",
)
def crear_rutina(rutina: schemas.RutinaCreate, db: Session = Depends(get_db)):
    """
    Crea una rutina y asocia los ejercicios indicados con su volumen:
    **series**, **repeticiones** y **peso soportado** (kg).

    Todos los `ejercicio_id` referenciados deben existir en el catálogo.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == rutina.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    db_rutina = models.Rutina(nombre=rutina.nombre, usuario_id=rutina.usuario_id)
    db.add(db_rutina)
    db.flush()

    for item in rutina.ejercicios:
        ejercicio = db.query(models.Ejercicio).filter(
            models.Ejercicio.id == item.ejercicio_id
        ).first()
        if not ejercicio:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ejercicio con id={item.ejercicio_id} no encontrado en el catálogo",
            )
        db.add(models.EjercicioRutina(rutina_id=db_rutina.id, **item.model_dump()))

    db.commit()
    db.refresh(db_rutina)
    return db_rutina


@app.get(
    "/rutinas/usuario/{usuario_id}",
    response_model=List[schemas.RutinaOut],
    status_code=status.HTTP_200_OK,
    tags=["Entrenamiento"],
    summary="Obtener rutinas de un usuario",
    response_description="Lista de rutinas con ejercicios, series y repeticiones",
)
def obtener_rutinas_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Lista todas las rutinas de entrenamiento del usuario con el detalle de cada ejercicio."""
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
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
    response_description="Alimento creado con su id asignado",
)
def crear_alimento(alimento: schemas.AlimentoCreate, db: Session = Depends(get_db)):
    """
    Crea un alimento en el catálogo maestro con su información nutricional
    por ración estándar: **calorías** (kcal) y **proteína** (g).
    """
    db_alimento = models.Alimento(**alimento.model_dump())
    db.add(db_alimento)
    db.commit()
    db.refresh(db_alimento)
    return db_alimento


@app.get(
    "/alimentos/",
    response_model=List[schemas.AlimentoOut],
    status_code=status.HTTP_200_OK,
    tags=["Nutrición"],
    summary="Listar catálogo de alimentos",
    response_description="Lista completa de alimentos disponibles con su información nutricional",
)
def listar_alimentos(db: Session = Depends(get_db)):
    """
    Devuelve todos los alimentos disponibles en el catálogo maestro,
    ordenados por nombre, con sus valores nutricionales por ración.
    """
    return db.query(models.Alimento).order_by(models.Alimento.nombre).all()


# ===========================================================================
# NUTRICIÓN — Registro Diario
# ===========================================================================

@app.post(
    "/registros-diarios/{usuario_id}/agregar-alimento",
    response_model=schemas.RegistroDiarioOut,
    status_code=status.HTTP_200_OK,
    tags=["Nutrición"],
    summary="Registrar consumo de un alimento en el día actual",
    response_description="Registro diario actualizado con los nuevos totales",
)
def agregar_alimento_registro(
    usuario_id: int,
    payload: schemas.RegistroAlimentoCreate,
    db: Session = Depends(get_db),
):
    """
    Agrega un alimento (con sus porciones) al `RegistroDiario` de hoy.

    - Si no existe un registro para la fecha actual, se crea automáticamente.
    - `total_calorias` y `total_proteinas` se recalculan en cada llamada
      multiplicando los valores del alimento por las porciones indicadas.
    - Enviar `porciones: 0.5` equivale a media ración.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    alimento = db.query(models.Alimento).filter(models.Alimento.id == payload.alimento_id).first()
    if not alimento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alimento no encontrado en el catálogo")

    hoy = date.today()

    registro = db.query(models.RegistroDiario).filter(
        models.RegistroDiario.usuario_id == usuario_id,
        models.RegistroDiario.fecha == hoy,
    ).first()

    if not registro:
        registro = models.RegistroDiario(usuario_id=usuario_id, fecha=hoy)
        db.add(registro)
        db.flush()

    db.add(models.RegistroAlimento(
        registro_diario_id=registro.id,
        alimento_id=payload.alimento_id,
        porciones=payload.porciones,
    ))

    registro.total_calorias  += int(alimento.calorias_por_racion * payload.porciones)
    registro.total_proteinas += alimento.proteina_por_racion * payload.porciones

    db.commit()
    db.refresh(registro)
    return registro


@app.get(
    "/registros-diarios/{usuario_id}/historial",
    response_model=List[schemas.HistorialItemOut],
    status_code=status.HTTP_200_OK,
    tags=["Nutrición"],
    summary="Consultar historial nutricional del usuario",
    response_description="Lista cronológica de registros diarios con calorías y proteínas",
)
def historial_registros(usuario_id: int, db: Session = Depends(get_db)):
    """
    Devuelve el historial completo de registros diarios del usuario,
    ordenado por fecha descendente (más reciente primero).

    Cada entrada muestra la fecha, el total de calorías consumidas
    y el total de proteínas, permitiendo visualizar la evolución
    nutricional a lo largo del tiempo.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    registros = (
        db.query(models.RegistroDiario)
        .filter(models.RegistroDiario.usuario_id == usuario_id)
        .order_by(models.RegistroDiario.fecha.desc())
        .all()
    )
    return registros


# ===========================================================================
# ANÁLISIS AGÉNTICO
# ===========================================================================

@app.get(
    "/registros-diarios/{usuario_id}/analisis-agente",
    response_model=schemas.AgenteResponse,
    status_code=status.HTTP_200_OK,
    tags=["Agente"],
    summary="Obtener retroalimentación agéntica del día actual",
    response_description="Análisis personalizado del balance nutricional con recomendaciones ODS 3",
)
def analisis_agente(usuario_id: int, db: Session = Depends(get_db)):
    """
    Ejecuta el motor agéntico sobre el `RegistroDiario` del día actual
    y devuelve retroalimentación personalizada alineada al **ODS 3: Salud y Bienestar**.

    El agente evalúa:
    - Balance calórico: consumido vs. meta del usuario.
    - Balance proteico: consumido vs. meta del usuario.
    - Genera un mensaje accionable con recomendaciones concretas.

    Si el usuario aún no ha registrado alimentos hoy, el análisis parte
    de cero y lo motiva a comenzar su registro.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    hoy = date.today()

    registro = db.query(models.RegistroDiario).filter(
        models.RegistroDiario.usuario_id == usuario_id,
        models.RegistroDiario.fecha == hoy,
    ).first()

    if not registro:
        # Registro sintético en memoria: no se persiste, solo alimenta al agente
        registro = models.RegistroDiario(
            usuario_id=usuario_id,
            fecha=hoy,
            total_calorias=0,
            total_proteinas=0.0,
        )

    return evaluar_registro_diario_agente(usuario, registro)
