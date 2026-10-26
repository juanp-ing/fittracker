# PDR — Documento de Requisitos del Producto: FitTracker Web App

## 1. Visión y Propósito del Producto
**FitTracker** es una aplicación web *mobile-first* diseñada para eliminar la fricción en el registro de entrenamientos de fuerza en el gimnasio. Su objetivo central de experiencia de usuario (UX) es permitir que un atleta registre una serie completa (ejercicio, peso en kilogramos y repeticiones) en **menos de 10 segundos**, operando con **una sola mano (pulgar)** y **sin desplegar el teclado virtual del teléfono**.

---

## 2. Decisiones Arquitectónicas y Reglas de Negocio Cerradas

1. **Tema Visual Oficial (`DESIGN.md`)**:
   - **Light Theme Gamificado de Duolingo** sobre superficie plana `#ffffff` (`--color-paper-white`), tipografía redondeada (`Nunito` 800/900 y `Nunito Sans` 500/700) y botones táctiles 3D con borde inferior sólido de `4px` y compresión física (`transform: translateY(2px)`).
   - Paleta semántica estricta:
     - `--color-eager-green: #58cc02` (CTA primario «¡SERIE TERMINADA!», PR logrado, músculo primario).
     - `--color-storybook-green: #d7ffb8` (fondos suaves de énfasis y pestaña activa).
     - `--color-spark-blue: #1cb0f6` (acciones secundarias y cronómetro de descanso activo).
     - `--color-fresh-leaf: #a5ed6e` (músculo secundario en el mapa anatómico SVG).
2. **Separación Estricta en 5 Capas (`AGENTS.md`)**:
   - `controllers/` → `services/` + `patterns/` → `repositories/` → `models/`.
   - Ningún controlador o plantilla realiza consultas SQLAlchemy directamente.
3. **Regla de Oro de Récord Personal (PR)**:
   - La estrategia principal (`PesoMaximoStrategy`) registra un nuevo PR cuando `nuevo_peso > max_peso_historico` del usuario en ese ejercicio (incluyendo la primera serie histórica donde el máximo previo es `0`).
   - La estrategia secundaria (`VolumenSerieStrategy`) evalúa `peso * repeticiones > max_volumen_historico`.
4. **Regla de Resumen Mensual (30 días vs. días 31–60)**:
   - `"MEJORO"`: `max_peso_actual > max_peso_previo` o (`max_peso_actual == max_peso_previo` y `max_vol_actual > max_vol_previo`).
   - `"ESTANCADO"`: entrenado en `>= 2` sesiones durante los últimos 30 días y sin superar el peso ni el volumen del periodo previo (días 31–60).
   - `"SIN_DATOS"`: menos de 2 sesiones en los últimos 30 días y sin marca superior al mes previo.

---

## 3. Matriz de Trazabilidad de Requisitos Funcionales (`RF-01` .. `RF-16`)

| Código | Requisito Funcional | Capa / Componente Implementado | Pruebas Automatizadas |
| :--- | :--- | :--- | :--- |
| **RF-01** | Registro de usuario con nombre, email único y contraseña segura (`>= 6` caracteres). | `AuthService.registrar_usuario`, `UsuarioRepository`, `POST /api/auth/register` | `test_auth_and_ejercicios_api.py` |
| **RF-02** | Inicio y cierre de sesión con persistencia mediante `Flask-Login`. | `AuthService.autenticar_usuario`, `POST /api/auth/login`, `POST /api/auth/logout` | `test_auth_and_ejercicios_api.py` |
| **RF-03** | Catálogo inicial en español con 10 grupos musculares y 23 ejercicios predeterminados. | `app/seeds/initial_data.py` (`seed_database`, comando `flask seed`) | `test_auth_and_ejercicios_api.py`, `test_workout_e2e_flow.py` |
| **RF-04** | Buscador instantáneo de ejercicios (`0ms` en memoria + filtro API `q`). | `EjercicioService.buscar_ejercicios`, `GET /api/ejercicios`, `static/js/buscador.js` | `test_auth_and_ejercicios_api.py` |
| **RF-05** | Registro de serie (peso y repeticiones) con botones gigantes `+/-` sin teclado. | `SesionService.registrar_serie`, `POST /api/sesiones/<id>/series`, `static/js/registro.js` | `test_rutinas_and_sesiones_api.py`, `test_workout_e2e_flow.py` |
| **RF-06** | Pre-carga automática del último peso y repeticiones usados por el usuario en cada ejercicio. | `SesionRepository.obtener_ultima_serie_ejercicio`, `EjercicioService.buscar_ejercicios` | `test_repositories.py`, `test_auth_and_ejercicios_api.py` |
| **RF-07** | Creación rápida de ejercicio personalizado al vuelo con músculos primarios y secundarios. | `EjercicioFactory.crear_personalizado`, `POST /api/ejercicios`, Bottom Sheet en `index.html` | `test_ejercicio_factory.py`, `test_auth_and_ejercicios_api.py` |
| **RF-08** | Gestión de rutinas personalizadas con orden de ejercicios y descanso configurable. | `RutinaService`, `RutinaRepository`, `POST /GET /DELETE /api/rutinas` | `test_rutinas_and_sesiones_api.py` |
| **RF-09** | Marcado de rutina favorita única por usuario e inicio de sesión libre o guiada. | `RutinaRepository.marcar_favorita`, `POST /api/rutinas/<id>/favorita`, `POST /api/sesiones` | `test_rutinas_and_sesiones_api.py` |
| **RF-10** | Detección automática de Récord Personal (PR) al guardar serie y celebración visual. | `PesoMaximoStrategy`, `PRDetectionObserver`, `celebrarNuevoPR` (`registro.js`) | `test_pr_and_state_patterns.py`, `test_workout_e2e_flow.py` |
| **RF-11** | Asociación explícita de grupos musculares primarios (`es_primario=True`) y secundarios (`False`). | Modelo `EjercicioGrupo`, `EjercicioRepository` | `test_models.py`, `test_repositories.py` |
| **RF-12** | Cronómetro automático de descanso post-serie basado en timestamps `Date.now()`. | `static/js/cronometro.js`, retorno `descanso_segundos` en `POST /api/sesiones/<id>/series` | `test_rutinas_and_sesiones_api.py`, `test_frontend_views.py` |
| **RF-13** | Mapa muscular anatómico SVG bicolor (`#58cc02` primarios, `#a5ed6e` secundarios). | `ResumenService.obtener_mapa_muscular`, `GET /api/mapa-muscular`, `static/js/mapa.js` | `test_resumen_api.py`, `test_workout_e2e_flow.py` |
| **RF-14** | Gráfica de evolución temporal de peso máximo y volumen por ejercicio. | `ResumenService.obtener_progreso_ejercicio`, `GET /api/progreso/<id>`, `static/js/graficas.js` | `test_resumen_api.py`, `test_workout_e2e_flow.py` |
| **RF-15** | Resumen mensual automático (30d vs. 31–60d) clasificando ejercicios en `MEJORO` y `ESTANCADO`. | `ComparacionMensualStrategy`, `ResumenFacade`, `GET /api/resumen-mensual` | `test_resumen_strategy.py`, `test_resumen_api.py` |
| **RF-16** | Cierre inmutable de sesión de entrenamiento e historial cronológico de sesiones. | `SesionActivaState` / `SesionFinalizadaState`, `PATCH /api/sesiones/<id>/finalizar`, `GET /api/historial` | `test_pr_and_state_patterns.py`, `test_resumen_api.py` |

---

## 4. Matriz de Requisitos No Funcionales (`RNF-01` .. `RNF-09`)

| Código | Requisito No Funcional | Implementación y Verificación |
| :--- | :--- | :--- |
| **RNF-01** | **Velocidad de Registro (`< 10s`)**: registrar una serie completa en menos de 10 segundos con una mano. | Controles gigantes `+/-` (`58px × 64px`), chips de incremento (`1`, `2.5`, `5 kg`) y pre-carga automática del último peso/reps. |
| **RNF-02** | **Ergonomía Mobile-First**: objetivos táctiles `>= 48px`, `touch-action: manipulation`, sin zoom accidental. | Token `--touch-target-min: 48px`, contenedor `.mobile-shell` (`430px`) y navegación fija en zona del pulgar. |
| **RNF-03** | **Concurrencia en SQLite**: modo WAL y claves foráneas activas en cada conexión. | Listener `@event.listens_for(Engine, "connect")` ejecutando `PRAGMA journal_mode=WAL;` y `PRAGMA foreign_keys=ON;` (`test_health.py`). |
| **RNF-04** | **Arquitectura Limpia y Patrones GoF**: separación en 5 capas y 5 patrones de diseño aplicados al dominio. | `Factory`, `Strategy`, `Observer`, `State` y `Facade` implementados en `app/patterns/`. |
| **RNF-05** | **Seguridad y Aislamiento Multi-usuario**: contraseñas hasheadas con Werkzeug y validación de pertenencia (`404`/`401`). | `generate_password_hash`, `check_password_hash` y pruebas de aislamiento entre usuarios (`test_seguridad_multiusuario_rutinas_y_sesiones`). |
| **RNF-06** | **Portabilidad y Contenedores**: despliegue reproducible con Docker y Gunicorn. | `Dockerfile`, `docker-compose.yml` con volumen persistente y healthcheck contra `/api/health`. |
| **RNF-07** | **Calidad y Cobertura de Pruebas**: suite automatizada con `pytest` y `sqlite:///:memory:`. | 43 pruebas automatizadas (unitarias, integración y funcionales E2E) con cobertura `> 90%`. |
| **RNF-08** | **Integración Continua (CI) y Flujo Git**: pipeline automatizado en GitHub Actions y ramas por funcionalidad. | `.github/workflows/tests.yml` e historial de merges `--no-ff` en `main`. |
| **RNF-09** | **Tolerancia a Fallos de Red en Gimnasio (Cola Offline)**: encolamiento local y resincronización automática. | Cola en `localStorage` (`fittracker_offline_series_queue`) y listener `window.addEventListener('online', ...)` en `registro.js`. |
