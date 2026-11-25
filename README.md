# 🏋️‍♂️🥗 NutriGym Agent — Solución Agéntica para el Bienestar y la Salud Sustentable

**NutriGym Agent** es una plataforma backend inteligente desarrollada en el marco del **Hackathon de Desarrollo Sustentable**, alineada con el **Objetivo de Desarrollo Sostenible 3 (ODS 3: Salud y Bienestar)** de la ONU.

El sistema unifica el seguimiento del entrenamiento de fuerza y el control nutricional diario (calorías y proteínas) bajo una arquitectura modular orientada a objetos, incorporando un **motor agéntico** capaz de evaluar el progreso diario del usuario frente a sus metas y generar retroalimentación personalizada en lenguaje natural.

---

## 🎯 Problema que Resuelve

Muchas personas abandonan sus objetivos de salud física porque llevan registros fragmentados (una aplicación para rutinas, otra para calorías, o notas manuales) sin recibir retroalimentación oportuna ni orientación adaptada a sus metas. **NutriGym Agent** centraliza ambos pilares en una sola API REST y añade un agente inteligente que interpreta las métricas diarias para promover hábitos sostenibles, recuperación muscular y prevención de riesgos metabólicos.

---

## ✨ Funcionalidades Principales

* **Gestión de Usuarios y Metas:** Registro de atletas con peso corporal y objetivos diarios personalizados de calorías y proteínas.
* **Catálogo y Rutinas de Entrenamiento:** Creación de ejercicios por grupo muscular y armado de rutinas con registro de series, repeticiones y peso soportado.
* **Control Nutricional Diario:** Catálogo de alimentos por ración y bitácora diaria con cálculo automático acumulado de kilocalorías y gramos de proteína.
* **Seguimiento de Progreso:** Consulta de rutinas, historial nutricional diario y actualización de peso corporal.
* **Motor Agéntico Inteligente (ODS 3):** Análisis automatizado del balance calórico y proteico (con margen de tolerancia óptima del ±5 %) que entrega recomendaciones accionables en lenguaje natural.

---

## 🏗️ Arquitectura y Estructura del Proyecto

El proyecto sigue una arquitectura modular separando responsabilidades entre persistencia, modelado ORM, validación de esquemas, lógica agéntica y enrutamiento REST:

```text
├── nutrigym_backend/
│   ├── __init__.py       # Inicialización del paquete
│   ├── database.py       # Configuración de SQLite y gestión de sesiones SQLAlchemy
│   ├── models.py         # Modelos ORM (Usuario, Ejercicio, Rutina, EjercicioRutina, Alimento, RegistroDiario, RegistroAlimento)
│   ├── schemas.py        # Validación y serialización con Pydantic v2
│   ├── agent.py          # Motor de lógica agéntica alineado al ODS 3
│   ├── main.py           # Aplicación FastAPI y endpoints REST
│   └── seed.py           # Datos iniciales de demostración (opcional)
├── docs/                 # Documento de Visión y Alcances (IBM DOORS Next) y Diagramas UML
├── requirements.txt      # Dependencias del proyecto
├── .gitignore            # Exclusión de archivos temporales y BD local
└── README.md             # Documentación principal del repositorio
