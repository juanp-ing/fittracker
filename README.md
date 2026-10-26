# FitTracker Web App

Aplicación web **mobile-first** diseñada para registrar entrenamientos de gimnasio (series, repeticiones y peso) en **menos de 10 segundos** y **sin necesidad de utilizar el teclado del teléfono móvil**.

---

## 1. Visión y Regla de Oro de UX

- **Operación con una sola mano (pulgar):** Interfaz optimizada para pantallas móviles con botones táctiles grandes (`+/-`) para ajustar peso y repeticiones a partir de la última serie registrada.
- **Cero recargas de página:** Todas las operaciones durante el entrenamiento se ejecutan mediante peticiones `fetch` asíncronas sobre una API REST JSON.
- **Seguimiento integral:** Mapa muscular anatómico en SVG (músculos primarios y secundarios), cronómetro de descanso automático, detección automática de Récords Personales (PR) y Resumen Mensual.

---

## 2. Stack Tecnológico

- **Backend:** Python 3.11+, Flask, Flask-SQLAlchemy (ORM), Flask-Login, Flask-Migrate, Gunicorn.
- **Base de Datos:** SQLite con modo `WAL` (`PRAGMA journal_mode=WAL;`) e integridad referencial activa (`PRAGMA foreign_keys=ON;`). En pruebas automatizadas se utiliza `sqlite:///:memory:`.
- **Frontend:** HTML5 (Jinja2 templates), CSS3 Mobile-First nativo, JavaScript Vanilla modular (`fetch`, `localStorage`, SVG inline, Chart.js).
- **Calidad y DevOps:** `pytest`, `pytest-cov`, Docker, Docker Compose y GitHub Actions (`tests.yml`).

---

## 3. Arquitectura en Capas y Patrones de Diseño

El proyecto aplica una separación estricta de responsabilidades (prohibido saltar capas):

```text
fittracker/
├── app/
│   ├── __init__.py                  # Application Factory: create_app(config_name)
│   ├── config/                      # Configuraciones (Development, Testing, Production)
│   ├── models/                      # Modelos SQLAlchemy y relaciones (9 tablas)
│   ├── repositories/                # Consultas y persistencia en base de datos
│   ├── services/                    # Lógica de negocio pura (agnóstica a HTTP)
│   ├── patterns/                    # Patrones GoF aplicados al dominio
│   │   ├── factory/                 # Creación de Ejercicios (Sistema vs. Usuario)
│   │   ├── strategy/                # Cálculo de PR y clasificación de Resumen Mensual
│   │   ├── observer/                # Eventos post-guardado de Serie (evaluación de PR)
│   │   ├── state/                   # Ciclo de vida de la Sesión (Activa, Finalizada)
│   │   └── facade/                  # Agregador para Resumen Mensual y Dashboard
│   ├── controllers/                 # Blueprints Flask (Vistas HTML + API JSON /api/...)
│   ├── seeds/                       # Catálogo inicial de grupos musculares y ejercicios
│   ├── templates/                   # Plantillas Jinja2 mobile-first
│   └── static/                      # Recursos estáticos (css/, js/, img/)
├── tests/                           # Suite de pruebas (unit/, integration/, functional/)
├── docs/                            # Documentación técnica (requirements, uml, architecture)
├── migrations/                      # Migraciones de base de datos
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.py
└── run.py
```

---

## 4. Instalación y Ejecución Local

### Opción A: Entorno Virtual (`.venv`)

```bash
# 1. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar el servidor de desarrollo (puerto 5000)
python run.py
```

La aplicación estará disponible en `http://localhost:5000` y el endpoint de diagnóstico en `http://localhost:5000/api/health`.

### Opción B: Docker y Docker Compose

```bash
docker compose up --build -d
```

El contenedor expone la aplicación en `http://localhost:5000` y persiste la base de datos SQLite en el volumen `sqlite_data`.

---

## 5. Ejecución de Pruebas Automatizadas

Para ejecutar toda la suite de pruebas (`unit`, `integration`, `functional`) sobre SQLite en memoria:

```bash
.venv/bin/pytest -v
```

Para ejecutar con reporte de cobertura:

```bash
.venv/bin/pytest --cov=app -v
```
