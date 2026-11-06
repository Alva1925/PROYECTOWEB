# ============================================================
# database.py
# Configuración del motor SQLite y la sesión de SQLAlchemy.
# El archivo nutrigym.db se crea automáticamente en la raíz
# del proyecto al iniciar la aplicación.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de conexión a SQLite. La ruta relativa "./nutrigym.db"
# crea el archivo en el directorio desde donde se ejecuta uvicorn.
SQLALCHEMY_DATABASE_URL = "sqlite:///./nutrigym.db"

# check_same_thread=False es necesario para SQLite con FastAPI
# porque las peticiones pueden llegar desde hilos distintos.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Fábrica de sesiones: cada petición HTTP obtendrá su propia sesión.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán todos los modelos ORM.
Base = declarative_base()


# ---------------------------------------------------------------------------
# Dependencia de FastAPI: inyecta una sesión de BD por petición y la cierra
# automáticamente al terminar, garantizando que no queden conexiones abiertas.
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
