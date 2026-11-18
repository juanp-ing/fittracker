# FitTracker Web App 🏋️‍♂️

> **Aplicación web mobile-first para registrar entrenamientos de gimnasio en menos de 10 segundos con una sola mano y sin usar el teclado del móvil.**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/framework-Flask%203.0%2B-black.svg)](https://flask.palletsprojects.com/)
[![Base de datos](https://img.shields.io/badge/database-SQLite%20%7C%20Postgres-orange.svg)](https://www.sqlite.org/wal.html)
[![Docker](https://img.shields.io/badge/container-Docker%20%2B%20Compose-2496ED.svg)](https://www.docker.com/)
[![Style](https://img.shields.io/badge/design-Duolingo%20claro%20y%20oscuro-58cc02.svg)](DESIGN.md)
[![Tests](https://github.com/juanp-ing/fittracker/actions/workflows/tests.yml/badge.svg)](https://github.com/juanp-ing/fittracker/actions/workflows/tests.yml)
[![Demo en línea](https://img.shields.io/badge/demo-fittracker--pi--three.vercel.app-000.svg)](https://fittracker-pi-three.vercel.app)

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
│   ├── seeds/             # Catálogo de 104 ejercicios y 12 Rutinas Famosas con plan por día
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

### 🔐 Registro y Wizard de Onboarding Biométrico
- Registro directo: al crear la cuenta se inicia sesión y se pasa al onboarding (la verificación por correo con código OTP se retiró; nunca salió de beta).
- Wizard de onboarding interactivo en **4 ventanas independientes** con micro-transiciones suaves (`180ms`):
  1. **Silueta:** Selección de fisionomía masculina o femenina.
  2. **Cuerpo:** Control táctil de peso y porcentaje de grasa corporal con tarjetas visuales de referencia rápida.
  3. **Meta:** Bajar de peso, Definir músculo o Ganar masa muscular.
  4. **Tipo:** Somatotipo metabólico (Ectomorfo, Mesomorfo, Endomorfo).

### 📋 Mini-Calendario Semanal, Checklist POP y Recordatorio de Hidratación
- Strip semanal de 7 días con punto indicador de actividad.
- Checklist táctil diario para tachar ejercicios con animación POP, tachado visual y vibración háptica.
- Modal de felicitación al completar todas las series con recordatorio inteligente de hidratación.

### 🌟 Catálogo de 104 Ejercicios y 12 Rutinas Famosas
- Catálogo de 104 ejercicios predeterminados en español (pesos libres, poleas y máquinas de un gimnasio comercial).
- 12 rutinas famosas (*Push Pull Legs*, *Torso-Pierna*, *PHUL*, *Arnold Split*, *StrongLifts 5x5*, etc.), cada una con su plan real por día: ejercicios distintos cada día y un nombre para cada entrenamiento («Empuje A», «Pierna B»…). Se recomiendan según complexión y meta y se añaden a la cuenta en un toque.
- Las rutinas propias también pueden tener ejercicios distintos cada día (interruptor «Ejercicios distintos cada día» del editor); «Hoy» muestra solo los que tocan ese día.

---

## 5. Cómo ejecutar el proyecto

Hay tres formas. Para evaluarlo, la más rápida es la **0** (no instala nada) y la más completa la **A** (Docker).

### 0. Usarlo en línea (sin instalar nada)

La app está desplegada en Vercel con una base de datos Postgres (Neon):

👉 **https://fittracker-pi-three.vercel.app**

Entra en **«Crear cuenta nueva»**: el registro no pide verificación de correo y te lleva directamente al onboarding. Se ve mejor en el móvil, o en el navegador con la vista de dispositivo (F12 → `Ctrl+Shift+M`).

---

### A. Con Docker (recomendado para evaluar)

**Requisitos:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows o macOS) o Docker Engine con el plugin Compose (Linux), abierto y en marcha. No hace falta instalar Python.

**1. Descargar el proyecto**

```bash
git clone https://github.com/juanp-ing/fittracker.git
cd fittracker
```

**2. Crear el archivo `.env` con la clave secreta.** La app se niega a arrancar en modo producción sin una `SECRET_KEY` propia. Basta con copiar la plantilla:

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell o CMD)
copy .env.example .env
```

Puedes dejar el valor de ejemplo para probar en tu equipo. Si lo vas a exponer en internet, cámbialo por uno aleatorio: `python -c "import secrets; print(secrets.token_hex(32))"`.

**3. Construir y arrancar**

```bash
docker compose up --build -d
```

La primera vez tarda uno o dos minutos (descarga la imagen de Python e instala las dependencias). Al arrancar, la app crea la base de datos y carga sola el catálogo: 10 grupos musculares, 104 ejercicios y 12 rutinas famosas.

**4. Abrir la app:** 👉 **http://localhost:5000** y crea una cuenta en «Crear cuenta nueva».

**Comandos útiles**

| Qué | Comando |
|---|---|
| Ver los registros (logs) | `docker compose logs -f` |
| Parar (conserva los datos) | `docker compose down` |
| Volver a arrancar | `docker compose up -d` |
| Borrar también los datos y empezar de cero | `docker compose down -v` |

Los datos se guardan en el volumen de Docker `sqlite_data`, así que sobreviven a reinicios.

**Problemas frecuentes**

| Síntoma | Solución |
|---|---|
| `Define SECRET_KEY en el archivo .env` | Falta el paso 2: crea `.env` a partir de `.env.example`. |
| `port is already allocated` / el puerto 5000 está ocupado (en macOS lo usa AirPlay) | En `docker-compose.yml`, cambia `"5000:5000"` por `"5001:5000"` y abre http://localhost:5001. |
| `Cannot connect to the Docker daemon` | Abre Docker Desktop (o en Linux: `sudo systemctl start docker`) y repite el paso 3. |

---

### B. En local con Python (para desarrollar)

**Requisitos:** Python 3.11 o superior y Git.

```bash
# 1. Descargar el proyecto
git clone https://github.com/juanp-ing/fittracker.git
cd fittracker

# 2. Crear y activar un entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Arrancar (crea la base SQLite local y carga el catálogo y el usuario demo)
python run.py
```

Abre 👉 **http://localhost:5000**. En desarrollo existe un usuario de demostración:

- **Email:** `demo@fittracker.local`
- **Contraseña:** `FitTracker123!`

Este usuario **solo** se crea en desarrollo. En Docker y en el despliegue en línea no existe, porque su contraseña es pública.

---

## 6. Pruebas Automatizadas y Cobertura

FitTracker cuenta con una suite completa de pruebas unitarias, de integración y funcionales E2E ejecutadas sobre SQLite en memoria (`sqlite:///:memory:`):

```bash
# Ejecutar toda la suite con reporte detallado
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
