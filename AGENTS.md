# AGENTS.md — Reglas de Arquitectura y Contexto para FitTracker Web App

## 1. Visión y Objetivo Crítico de UX
FitTracker es una aplicación web mobile-first para registrar entrenamientos de gimnasio (series, repeticiones, peso) en menos de 10 segundos sin usar el teclado del móvil.
- **Regla de Oro UX:** Toda acción durante el entrenamiento debe ejecutarse con una sola mano (pulgar), botones grandes (`+/-`) y peticiones `fetch` asíncronas (0 recargas de página).

## 2. Stack Tecnológico Oficial
- **Backend:** Python 3.11+, Flask, SQLAlchemy (ORM), Flask-Login, Flask-Migrate.
- **Base de Datos:** SQLite en modo WAL (`PRAGMA journal_mode=WAL;`) y claves foráneas activas (`PRAGMA foreign_keys=ON;`). En pruebas se usa `sqlite:///:memory:`.
- **Frontend:** HTML5 (Jinja2 templates), CSS3 Mobile-First nativo, JavaScript Vanilla modular (`fetch`, `localStorage`, SVG inline, Chart.js).
- **Calidad y DevOps:** pytest (pruebas unitarias, integración y funcionales), Docker, Docker Compose, GitHub Actions (`tests.yml`).

## 3. Estructura de Directorios y Separación Estricta de Capas
Está TERMINANTEMENTE PROHIBIDO saltar capas (ej. hacer consultas SQLAlchemy dentro de un controlador o vista).

```text
fittracker/
├── app/
│   ├── __init__.py                  # Application Factory: create_app(config_name)
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # DevelopmentConfig, TestingConfig, ProductionConfig
│   ├── models/                      # SOLO definición de modelos SQLAlchemy y relaciones
│   ├── repositories/                # SOLO consultas y persistencia en base de datos (SQLAlchemy)
│   ├── services/                    # Lógica de negocio pura (agnóstica a HTTP/Flask request)
│   ├── patterns/                    # Patrones de diseño GoF aplicados al dominio
│   │   ├── factory/                 # Creación de Ejercicios (Sistema vs. Usuario)
│   │   ├── strategy/                # Estrategias de cálculo de PR y clasificación de Resumen Mensual
│   │   ├── observer/                # Eventos post-guardado de Serie (dispara evaluación de PR)
│   │   ├── state/                   # Ciclo de vida de la Sesión (Activa, Finalizada)
│   │   └── facade/                  # Agregador de datos para Resumen Mensual y Dashboard
│   ├── controllers/                 # Blueprints Flask (Rutas HTML + Endpoints API JSON `/api/...`)
│   ├── seeds/                       # Datos iniciales (Grupos musculares y ejercicios en español)
│   ├── templates/                   # Vistas Jinja2 mobile-first
│   └── static/                      # css/, js/ (buscador, registro, cronometro, mapa, graficas), img/
├── tests/
│   ├── unit/                        # Pruebas aisladas de services/ y patterns/
│   ├── integration/                 # Pruebas de repositories/ y API REST con SQLite en memoria
│   └── functional/                  # Flujos completos E2E
├── docs/                            # requirements/, uml/, scrum/, architecture/, testing/
├── migrations/
├── .github/workflows/tests.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.py
└── run.py
```
