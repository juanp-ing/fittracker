# Plan de Pruebas, Cobertura y Protocolo de Usabilidad (`< 10s`) — FitTracker

## 1. Estrategia de Pruebas Automatizadas (`pytest`)
La suite de pruebas de **FitTracker Web App** se ejecuta sobre una base de datos aislada en memoria (`sqlite:///:memory:`) con `PRAGMA foreign_keys=ON;` activo en cada conexión, garantizando rapidez (`< 3 segundos` para toda la suite) y determinismo total.

### Niveles de Prueba
1. **Pruebas Unitarias (`tests/unit/`)**:
   - `test_health.py`: verificación de `/api/health`, `PRAGMA foreign_keys=ON` y `PRAGMA journal_mode=WAL` en archivo SQLite real.
   - `test_models.py`: creación de las 9 tablas, índice compuesto `ix_pr_usuario_ejercicio_fecha`, hashing de contraseñas, cascadas `ON DELETE CASCADE` y propiedad calculada `Serie.volumen`.
   - `test_ejercicio_factory.py`: validaciones de dominio en `EjercicioFactory.crear_predeterminado` y `EjercicioFactory.crear_personalizado` (nombres vacíos, longitudes `> 120`, grupos primarios obligatorios, deduplicación).
   - `test_pr_and_state_patterns.py`: pruebas aisladas de `PesoMaximoStrategy`, `VolumenSerieStrategy`, `SesionActivaState` y `SesionFinalizadaState` (`SesionCerradaError`).
   - `test_resumen_strategy.py`: clasificación determinista de `ComparacionMensualStrategy` en `"MEJORO"`, `"ESTANCADO"` y `"SIN_DATOS"`.
2. **Pruebas de Integración (`tests/integration/`)**:
   - `test_repositories.py`: persistencia, búsquedas insensibles a mayúsculas, pre-carga de última serie y aislamiento por `usuario_id`.
   - `test_auth_and_ejercicios_api.py`: registro, login, logout, protección `401`, idempotencia de `seed_database()` y creación de ejercicios personalizados.
   - `test_rutinas_and_sesiones_api.py`: ciclo de vida de rutinas favoritas, sesiones, numeración automática de series, disparo de `PRDetectionObserver` y seguridad multi-usuario.
   - `test_resumen_api.py`: validación de contratos JSON en `/api/resumen-mensual`, `/api/mapa-muscular`, `/api/progreso/<id>` y `/api/historial`.
3. **Pruebas Funcionales End-to-End (`tests/functional/`)**:
   - `test_frontend_views.py`: renderizado del shell móvil, redirecciones de seguridad, micro-interacciones CSS/JS, tokens de `DESIGN.md` y soporte `@media (prefers-reduced-motion: reduce)`.
   - `test_workout_e2e_flow.py`: recorrido completo E2E de Mateo (semillas + login demo + registro + ejercicio personalizado + rutina favorita + 3 series con PR + cierre de sesión + mapa muscular bicolor + progreso + resumen mensual).

---

## 2. Ejecución de Pruebas y Reporte de Cobertura

Comando oficial de verificación:

```bash
pytest --cov=app --cov-report=term-missing -v
```

- **Total de pruebas**: `43 passed` (100% en verde).
- **Cobertura global del paquete `app/`**: `> 92%` en modelos, repositorios, servicios, patrones GoF, semillas y controladores.

---

## 3. Protocolo de Prueba de Usabilidad en Gimnasio (`< 10 Segundos` por Serie)

### Objetivo (RNF-01 y RNF-02)
Comprobar empíricamente que un usuario puede registrar una serie durante su entrenamiento en **menos de 10 segundos**, operando el teléfono con **una sola mano (pulgar)** y **sin abrir el teclado virtual**.

### Condiciones de la Prueba
- **Dispositivo**: Smartphone real o emulador móvil con viewport `390×844 px` (`<= 430px`).
- **Postura**: Sujeción con una sola mano; interacción exclusiva con el pulgar.
- **Escenario**: El usuario acaba de terminar una serie de *Press de banca con barra* subiendo `2.5 kg` respecto a su serie anterior y realizando `1 repetición` adicional.

### Cronometraje Paso a Paso (Presupuesto de Tiempo `< 10s`)

| Paso | Acción del Usuario (Pulgar) | Respuesta del Sistema | Tiempo Estimado |
| :--- | :--- | :--- | :--- |
| **1** | Toca el ejercicio en la lista reciente o rutina activa (pre-cargado con el último peso `80 kg` y `8 reps`). | Selección en `0ms` en memoria (`buscador.js`) y actualización instantánea de displays. | `1.2 s` |
| **2** | Toca una vez el botón gigante **`＋`** de Peso (`58×64 px`, paso activo `2.5 kg`). | Compresión táctil (`70ms`), incremento a `82.5 kg` y micro-pulso numérico sin abrir teclado. | `0.8 s` |
| **3** | Toca una vez el botón gigante **`＋`** de Repeticiones (`58×64 px`, paso `±1 rep`). | Compresión táctil (`70ms`), incremento a `9 reps` y micro-pulso numérico. | `0.8 s` |
| **4** | Toca el botón gigante verde **«¡SERIE TERMINADA!»** (`min-height: 62px`). | Envío asíncrono `fetch` (`0 recargas`), inicio inmediato del cronómetro de descanso y badge *spring* de nuevo PR. | `1.4 s` |
| **Total** | **4 toques de pulgar (0 uso de teclado)** | **Serie registrada + PR celebrado + Cronómetro corriendo** | **`4.2 segundos` (`< 10s` cumplido)** |

