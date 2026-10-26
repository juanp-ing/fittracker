# Planificación Ágil Scrum (Roadmap de 8 Sprints) — FitTracker Web App

## 1. Resumen Ejecutivo de la Metodología
El desarrollo de **FitTracker Web App** se estructuró en **8 Sprints incrementales**, aplicando integración continua (GitHub Actions), desarrollo guiado por pruebas (`pytest` con SQLite en memoria) y flujo de ramas por funcionalidad (`feature/*` fusionadas con `--no-ff` en `main`).

---

## 2. Desglose de Sprints y Entregables

| Sprint | Enfoque Principal | Historias / Requisitos Cubiertos | Entregables Verificables | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Sprint 1** | **Scaffolding, Configuración e Infraestructura Base** | `RNF-03`, `RNF-06`, `RNF-08` | Application Factory (`create_app`), configuración por entornos (`Development`, `Testing`, `Production`), listener `PRAGMA journal_mode=WAL` y `PRAGMA foreign_keys=ON`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/tests.yml` y endpoint `/api/health`. | Completado |
| **Sprint 2** | **Modelado de Datos SQLAlchemy e Integridad Referencial** | `RF-01`, `RF-11`, `RNF-05` | 9 tablas relacionales (`usuarios`, `grupos_musculares`, `ejercicios`, `ejercicio_grupos`, `rutinas`, `rutina_ejercicios`, `sesiones`, `series`, `prs`), propiedad calculada `Serie.volumen` e índice compuesto `ix_pr_usuario_ejercicio_fecha`. | Completado |
| **Sprint 3** | **Capa de Repositorios y Contratos de API REST** | `RNF-04`, `RNF-05` | `UsuarioRepository`, `EjercicioRepository`, `RutinaRepository`, `SesionRepository`, `PRRepository` con aislamiento estricto por `usuario_id` y especificación `docs/architecture/api_contracts.md`. | Completado |
| **Sprint 4** | **Autenticación, Catálogo en Español, Factory y Semillas** | `RF-01`, `RF-02`, `RF-03`, `RF-04`, `RF-07` | `EjercicioFactory` (`crear_predeterminado`, `crear_personalizado`), `seed_database()` con 10 grupos musculares y 23 ejercicios en español, `AuthService`, `EjercicioService`, `auth_bp` y `ejercicio_bp`. | Completado |
| **Sprint 5** | **Rutinas, Sesiones, Detección de PRs y Patrones State / Strategy / Observer** | `RF-05`, `RF-06`, `RF-08`, `RF-09`, `RF-10`, `RF-12`, `RF-16` | `SesionState` (`ACTIVA` / `FINALIZADA`), `PesoMaximoStrategy`, `VolumenSerieStrategy`, `SerieSubject` + `PRDetectionObserver`, `RutinaService`, `SesionService`, `PRService`, `rutina_bp` y `sesion_bp`. | Completado |
| **Sprint 6** | **Motor de Resumen Mensual 30d, Mapa Muscular Bicolor y Patrón Facade** | `RF-13`, `RF-14`, `RF-15` | `ComparacionMensualStrategy` (`MEJORO`, `ESTANCADO`, `SIN_DATOS`), `ResumenService`, `ResumenFacade` y endpoints `/api/resumen-mensual`, `/api/mapa-muscular`, `/api/progreso/<id>` y `/api/historial`. | Completado |
| **Sprint 7** | **Frontend Mobile-First (Light Theme Duolingo) y Cola Offline** | `RNF-01`, `RNF-02`, `RNF-09` | Sistema de diseño `DESIGN.md` en `styles.css`, plantillas Jinja2 con contenedor `.mobile-shell` (`430px`), Bottom Nav fija y 5 módulos JS (`buscador.js`, `registro.js`, `cronometro.js`, `mapa.js`, `graficas.js`). | Completado |
| **Sprint 8** | **Micro-interacciones, Auditoría Determinista, E2E y Cierre Documental** | `RNF-01`, `RNF-02`, `RNF-07` | Feedback táctil instantáneo (`translateY(2px)`), celebración de PR con curva *spring*, soporte `@media (prefers-reduced-motion: reduce)`, auditoría `impeccable detect` (0 errores), flujo E2E de Mateo y documentación de ingeniería en `docs/`. | Completado |

---

## 3. Definición de Hecho (Definition of Done — DoD)
1. **Separación de capas intacta**: ningún controlador ni plantilla ejecuta consultas SQLAlchemy directamente.
2. **Pruebas automatizadas en verde**: 100% de las pruebas unitarias, de integración y funcionales E2E pasando en `pytest` sobre `sqlite:///:memory:`.
3. **Cobertura de código**: cobertura global del paquete `app/` superior al 90%.
4. **Calidad de interfaz móvil**: objetivos táctiles `>= 48px`, contraste WCAG AA/AAA sobre `#ffffff` y 0 advertencias/errores en el detector determinista `impeccable`.
