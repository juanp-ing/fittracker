# FitTracker Web App 🏋️‍♂️

> **Aplicación web mobile-first para registrar entrenamientos de gimnasio en menos de 10 segundos con una sola mano y sin usar el teclado del móvil.**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/framework-Flask%203.0%2B-black.svg)](https://flask.palletsprojects.com/)
[![SQLite WAL](https://img.shields.io/badge/database-SQLite%20WAL%20mode-orange.svg)](https://www.sqlite.org/wal.html)
[![Docker](https://img.shields.io/badge/container-Docker%20%2B%20Compose-2496ED.svg)](https://www.docker.com/)
[![Style](https://img.shields.io/badge/design-Duolingo%20Light%20Theme-58cc02.svg)](DESIGN.md)
[![Tests](https://img.shields.io/badge/tests-54%20passed%20%28100%25%29-brightgreen.svg)](tests/)

---

## 1. Visión y Regla de Oro de UX

FitTracker resuelve la fricción tradicional de las aplicaciones de fitness en el gimnasio: pantallas recargadas, interfaces oscuras difíciles de leer bajo focos de luz y la molestia de teclear números entre series con manos sudorosas.

- **Operación exclusiva con el pulgar:** Todos los controles críticos están ubicados en la zona natural de alcance del pulgar, con botones táctiles grandes (`+/-`), pasos configurables (`0.5 kg`, `1 kg`, `2.5 kg`, `5 kg`) y precarga automática de las métricas de la serie anterior.
- **Cero recargas de página:** Toda la interacción durante el entrenamiento se gestiona mediante peticiones `fetch` asíncronas contra endpoints REST JSON, garantizando transiciones instantáneas.
- **Micro-interacciones táctiles gamificadas:** Feedback de compresión mecánica inmediata (`transform: translateY(2px)`), explosión POP al tachar ejercicios, celebración *spring* al batir un Récord Personal (PR) y soporte nativo para `@media (prefers-reduced-motion: reduce)`.

---

## 2. Sistema de Diseño Duolingo Light Theme (`DESIGN.md`)

FitTracker implementa de manera estricta el **Light Theme Gamificado** sobre superficie plana `#ffffff`, auditado con la skill `impeccable` (**0 anti-patrones detectados**):

- **Paleta Cromática Oficial:**
  - `--color-eager-green: #58cc02`: Acciones primarias, series completadas, PRs y músculo primario.
  - `--color-storybook-green: #d7ffb8`: Fondos suaves de éxito, tarjetas seleccionadas y acentos activos.
  - `--color-spark-blue: #1cb0f6`: Acciones secundarias, cronómetro de descanso activo y navegación.
  - `--color-fresh-leaf: #a5ed6e`: Músculo secundario en el mapa anatómico y estado intermedio.
  - `--color-night-ink: #000437`: Tipografía de alto contraste sobre fondo blanco puro.
  - `--color-card-border: #e5e5e5`: Bordes nítidos de 2px con base 3D presionable de 4px.
- **Tipografía Redondeada:** `Nunito` (800 / 900) para titulares e interfaces de conteo y `Nunito Sans` (500 / 700) para lectura.
- **Objetivos Táctiles:** Tamaño mínimo de toque `>= 48px` (`--touch-target-min`) con separación ergonómica.

---

## 3. Arquitectura en 5 Capas y 5 Patrones de Diseño GoF

El backend aplica una separación arquitectónica estricta donde está **terminantemente prohibido saltar capas** (los controladores jamás ejecutan consultas ORM directas):

```text
fittracker/
├── app/
│   ├── models/            # SOLO definición de modelos SQLAlchemy (9 tablas relacionales)
│   ├── repositories/      # SOLO consultas y persistencia a SQLite con aislamiento por usuario
│   ├── services/          # Lógica de negocio pura (agnóstica a peticiones HTTP)
│   ├── patterns/          # 5 Patrones de Diseño GoF aplicados al dominio fitness
│   │   ├── factory/       # EjercicioFactory: Creación de ejercicios (Sistema vs. Personalizados)
│   │   ├── strategy/      # PRStrategy (Peso/Volumen) y ResumenStrategy (MEJORO/ESTANCADO/SIN_DATOS)
│   │   ├── observer/      # SerieSubject + PRDetectionObserver (evaluación desacoplada post-guardado)
│   │   ├── state/         # SesionState (Transiciones de ciclo de vida: Activa vs. Finalizada)
│   │   └── facade/        # ResumenFacade (Orquestador unificado de analítica y mapa muscular)
│   ├── controllers/       # Blueprints Flask (Rutas HTML Jinja2 + Endpoints API JSON /api/...)
│   ├── seeds/             # Catálogo de 40 ejercicios comerciales y 12 Rutinas Famosas
│   ├── templates/         # Vistas mobile-first con shell móvil de 430px (.mobile-shell)
│   └── static/            # CSS nativo, módulos JavaScript Vanilla (ES6+) e ilustraciones SVG
├── tests/                 # Suite de 54 pruebas automatizadas (unit/, integration/, functional/)
└── docs/                  # Documentación formal (requirements, architecture, scrum, uml, testing)
```

| Patrón GoF | Implementación en FitTracker | Propósito de Dominio |
| :--- | :--- | :--- |
| **Factory Method** | `EjercicioFactory` | Separa la creación de ejercicios del sistema de los personalizados por el usuario, validando normalización y grupos musculares primarios. |
| **Strategy** | `PRStrategy` & `ResumenStrategy` | Permite alternar algoritmos de récord (peso máximo vs. volumen) y comparar ventanas temporales (0-30 días vs. 31-60 días). |
| **Observer** | `PRDetectionObserver` | Escucha la persistencia de series para evaluar récords de forma asíncrona y desacoplada del controlador. |
| **State** | `SesionState` | Modela las fases de la sesión (`Activa` vs. `Finalizada`), bloqueando mutaciones en sesiones ya concluidas. |
| **Facade** | `ResumenFacade` | Provee una interfaz unificada y de alto nivel que combina estado muscular, volumen semanal, PRs y comparativas mensuales. |

---

## 4. Funcionalidades Destacadas (V2.0)

### 🗺️ Mapa Muscular Anatómico Vectorial en 4 Capas
- Ilustración vectorial continua dual (**Hombre / Mujer**) basada en trazados Bézier de alta precisión (`viewBox="0 0 500 520"`):
  - **Capa `<defs>`:** Gradientes volumétricos 3D (`#grad-muscle-primary`, `#grad-muscle-secondary`, `#grad-muscle-rest`), filtro de brillo `#muscle-glow` y máscaras `<clipPath>` por grupo.
  - **Capa 1 (Silueta y Tendones):** Contorno orgánico sin divisiones artificiales, inserciones tendinosas (clavículas, línea alba y fascia toracolumbar).
  - **Capa 2 (10 Grupos Musculares):** Vientres musculares interactivos (`Pecho`, `Espalda`, `Hombros`, `Bíceps`, `Tríceps`, `Cuádriceps`, `Isquiotibiales`, `Glúteos`, `Pantorrillas`, `Core`) coloreados dinámicamente según volumen reciente.
  - **Capa 3 (Fibras Musculares):** Estrías internas que siguen la orientación biomecánica real (abanico pectoral, multipennadas en deltoides, oblicuas en dorsales y glúteos).
  - **Capa 4 (Etiquetas Guía):** Capa interactiva estilo atlas anatómico con líneas indicadoras, activable con el chip **«🏷️ Nombres»**.
  - **Bottom Sheet Interactivo:** Toca cualquier músculo para consultar series realizadas, mejor PR histórico y ejercicios recomendados para entrenar hoy.

### 🔐 Verificación OTP y Wizard de Onboarding Biométrico
- Flujo de registro seguro con código OTP numérico de 6 dígitos con expiración automática.
- Wizard de onboarding interactivo en **4 ventanas independientes** con micro-transiciones suaves (`180ms`):
  1. **Silueta:** Selección de fisionomía masculina o femenina.
  2. **Cuerpo:** Control táctil de peso y porcentaje de grasa corporal con tarjetas visuales de referencia rápida.
  3. **Meta:** Bajar de peso, Definir músculo o Ganar masa muscular.
  4. **Tipo:** Somatotipo metabólico (Ectomorfo, Mesomorfo, Endomorfo).

### 📋 Mini-Calendario Semanal, Checklist POP y Recordatorio de Hidratación
- Strip semanal de 7 días con punto indicador de actividad.
- Checklist táctil diario para tachar ejercicios con animación POP, tachado visual y vibración háptica.
- Modal de felicitación al completar todas las series con recordatorio inteligente de hidratación.

### 🌟 Catálogo de 40 Ejercicios y 12 Rutinas Famosas
- Catálogo de 40 ejercicios predeterminados en español cubriendo todas las máquinas de un gimnasio comercial.
- Motor de 12 rutinas legendarias (*Push Pull Legs*, *Torso-Pierna*, *Arnold Split*, *PHAT*, *Starting Strength 5x5*, *German Volume Training*, etc.) recomendadas automáticamente según somatotipo y meta, clonables a la cuenta del usuario en un solo toque.

---

## 5. Instalación y Puesta en Marcha

### Prerrequisitos
- Python 3.11 o superior.
- Git.
- SQLite3.

### Opción A: Entorno Virtual Local

```bash
# 1. Clonar el repositorio y navegar a la carpeta
git clone https://github.com/<tu-usuario>/fittracker.git
cd fittracker

# 2. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar base de datos y sembrar catálogo con usuario demo
flask seed --demo

# 5. Iniciar la aplicación
python run.py
```

Accede desde tu navegador móvil o de escritorio a:
👉 **`http://localhost:5000`**

#### Credenciales del Usuario de Demostración:
- **Email:** `demo@fittracker.local`
- **Contraseña:** `FitTracker123!`

---

### Opción B: Despliegue con Docker y Docker Compose

Producción necesita una `SECRET_KEY` propia; sin ella el contenedor no arranca. Créala una sola vez en un archivo `.env` (está en `.gitignore`, no se sube al repositorio):

```bash
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env
```

```bash
# Construir y levantar el contenedor en segundo plano
docker compose up --build -d

# Ver logs en tiempo real
docker compose logs -f
```

La base de datos SQLite se almacena y persiste en el volumen `sqlite_data`. Para detener el servicio:
```bash
docker compose down
```

---

## 6. Pruebas Automatizadas y Cobertura

FitTracker cuenta con una suite completa de pruebas unitarias, de integración y funcionales E2E ejecutadas sobre SQLite en memoria (`sqlite:///:memory:`):

```bash
# Ejecutar las 54 pruebas con reporte detallado
pytest -v

# Ejecutar con análisis de cobertura de código
pytest --cov=app --cov-report=term-missing -v
```

### Integración Continua (CI)
El archivo [`.github/workflows/tests.yml`](.github/workflows/tests.yml) ejecuta automáticamente toda la suite de pruebas en cada `push` y `pull_request` contra la rama `main` en entornos Ubuntu con Python 3.11.

---

## 7. Documentación Técnica

La carpeta [`docs/`](docs/) contiene toda la ingeniería del proyecto:
- [`docs/requirements/pdr_fittracker.md`](docs/requirements/pdr_fittracker.md): Especificación de Requisitos de Software (RFs y RNFs).
- [`docs/architecture/api_contracts.md`](docs/architecture/api_contracts.md): Contratos OpenAPI/REST de todos los endpoints JSON.
- [`docs/uml/diagrams.md`](docs/uml/diagrams.md): Diagramas de Casos de Uso, Clases UML, Secuencia y Estados en Mermaid.
- [`docs/scrum/sprints_roadmap.md`](docs/scrum/sprints_roadmap.md): Planificación y desglose de los 12 Sprints de desarrollo ágil.
- [`docs/testing/test_plan_and_usability.md`](docs/testing/test_plan_and_usability.md): Plan de pruebas, matriz de casos de prueba y test de usabilidad (< 10 segundos).

---

## 8. Licencia

Este proyecto fue desarrollado bajo la metodología de ingeniería de software con Clean Architecture y patrones de diseño GoF. Distribuido bajo la Licencia MIT.
