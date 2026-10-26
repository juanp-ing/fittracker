# Contratos de API REST — FitTracker Web App (Sección 10.5 del PDR)

Este documento especifica el contrato formal de todos los endpoints JSON expuestos por la capa `app/controllers/` bajo el prefijo `/api/`. Todas las respuestas utilizan `Content-Type: application/json`.

---

## Convenciones Generales

### Formato de Error Estándar
```json
{
  "error": "Descripción legible del problema",
  "code": "CODIGO_ERROR"
}
```

### Códigos de Estado HTTP
| Código | Significado | Caso de Uso |
| :--- | :--- | :--- |
| `200 OK` | Operación exitosa | Lecturas (`GET`), actualizaciones (`PUT`/`PATCH`) y eliminaciones (`DELETE`). |
| `201 Created` | Recurso creado | Creación de usuarios, ejercicios, rutinas, sesiones o series (`POST`). |
| `400 Bad Request` | Datos inválidos | Validaciones de dominio fallidas (campos vacíos, pesos negativos, sesión ya finalizada). |
| `401 Unauthorized` | No autenticado | Sesión no iniciada o credenciales inválidas. |
| `403 Forbidden` | Sin permisos | Intento de acceder o modificar un recurso que pertenece a otro usuario. |
| `404 Not Found` | No encontrado | El recurso solicitado no existe o no es visible para el usuario. |

---

## 1. Diagnóstico (`/api/health`)

### `GET /api/health`
Verifica la disponibilidad del servidor y la configuración de SQLite WAL.
- **Autenticación:** Pública.
- **Response `200 OK`:**
```json
{
  "status": "ok",
  "app": "FitTracker",
  "wal_enabled": true
}
```

---

## 2. Autenticación (`/api/auth/*`)

### `POST /api/auth/registro`
Registra una nueva cuenta de usuario e inicia su sesión.
- **Request Body:**
```json
{
  "nombre": "Juan Pérez",
  "email": "juan@ejemplo.com",
  "password": "PasswordSegura123"
}
```
- **Response `201 Created`:**
```json
{
  "id": 1,
  "nombre": "Juan Pérez",
  "email": "juan@ejemplo.com",
  "mensaje": "Usuario registrado exitosamente"
}
```
- **Errores:** `400 Bad Request` (email duplicado, formato inválido o contraseña menor a 6 caracteres).

### `POST /api/auth/login`
Autentica un usuario mediante correo y contraseña.
- **Request Body:**
```json
{
  "email": "juan@ejemplo.com",
  "password": "PasswordSegura123"
}
```
- **Response `200 OK`:**
```json
{
  "id": 1,
  "nombre": "Juan Pérez",
  "email": "juan@ejemplo.com",
  "mensaje": "Sesión iniciada correctamente"
}
```
- **Errores:** `400 Bad Request` (campos faltantes), `401 Unauthorized` (credenciales inválidas).

### `POST /api/auth/logout`
Cierra la sesión activa del usuario.
- **Autenticación:** Requerida (`@login_required`).
- **Response `200 OK`:**
```json
{
  "mensaje": "Sesión cerrada correctamente"
}
```

---

## 3. Catálogo y Buscador de Ejercicios (`/api/ejercicios`)

### `GET /api/ejercicios`
Lista los ejercicios visibles para el usuario autenticado (predeterminados del sistema + creados por el propio usuario).
- **Autenticación:** Requerida.
- **Query Params:**
  - `q` (opcional, string): Texto de búsqueda parcial insensible a mayúsculas/minúsculas.
- **Response `200 OK`:**
```json
{
  "ejercicios": [
    {
      "id": 1,
      "nombre": "Press de Banca con Barra",
      "es_predeterminado": true,
      "grupos_primarios": [{"id": 1, "nombre": "Pecho"}],
      "grupos_secundarios": [{"id": 4, "nombre": "Tríceps"}, {"id": 3, "nombre": "Hombros"}]
    }
  ]
}
```

### `POST /api/ejercicios`
Crea un ejercicio personalizado para el usuario autenticado (vía `EjercicioFactory`).
- **Autenticación:** Requerida.
- **Request Body:**
```json
{
  "nombre": "Press Inclinado con Mancuernas Unilateral",
  "grupos_primarios_ids": [1],
  "grupos_secundarios_ids": [3, 4]
}
```
- **Response `201 Created`:**
```json
{
  "id": 42,
  "nombre": "Press Inclinado con Mancuernas Unilateral",
  "es_predeterminado": false,
  "creado_por": 1,
  "grupos_primarios_ids": [1],
  "grupos_secundarios_ids": [3, 4]
}
```
- **Errores:** `400 Bad Request` (nombre vacío o sin grupo muscular primario), `401 Unauthorized`.

---

## 4. Gestión de Rutinas (`/api/rutinas`)

### `GET /api/rutinas`
Lista las rutinas del usuario autenticado (con filtro opcional de favoritas).
- **Autenticación:** Requerida.
- **Query Params:** `favoritas=true|false` (opcional).
- **Response `200 OK`:**
```json
{
  "rutinas": [
    {
      "id": 10,
      "nombre": "Empuje (Push)",
      "es_favorita": true,
      "ejercicios": [
        {
          "ejercicio_id": 1,
          "nombre": "Press de Banca con Barra",
          "orden": 1,
          "descanso_segundos": 90,
          "series_objetivo": 4
        }
      ]
    }
  ]
}
```

### `POST /api/rutinas`
Crea una nueva rutina personalizada.
- **Autenticación:** Requerida.
- **Request Body:**
```json
{
  "nombre": "Empuje (Push)",
  "es_favorita": true,
  "ejercicios": [
    {
      "ejercicio_id": 1,
      "orden": 1,
      "descanso_segundos": 90,
      "series_objetivo": 4
    }
  ]
}
```
- **Response `201 Created`:** Objeto JSON de la rutina creada.
- **Errores:** `400 Bad Request` (nombre vacío o ejercicio inaccesible), `404 Not Found`.

### `PUT /api/rutinas/<int:rutina_id>`
Actualiza el nombre y/o los ejercicios de una rutina existente del usuario.
- **Autenticación:** Requerida.
- **Request Body:** Mismo esquema que `POST /api/rutinas`.
- **Response `200 OK`:** Objeto JSON de la rutina actualizada.
- **Errores:** `400 Bad Request`, `403 Forbidden`, `404 Not Found`.

### `PATCH /api/rutinas/<int:rutina_id>/favorita`
Alterna el indicador `es_favorita` de una rutina.
- **Autenticación:** Requerida.
- **Response `200 OK`:**
```json
{
  "id": 10,
  "es_favorita": false
}
```
- **Errores:** `403 Forbidden`, `404 Not Found`.

### `DELETE /api/rutinas/<int:rutina_id>`
Elimina una rutina del usuario.
- **Autenticación:** Requerida.
- **Response `200 OK`:**
```json
{
  "mensaje": "Rutina eliminada correctamente"
}
```
- **Errores:** `403 Forbidden`, `404 Not Found`.

---

## 5. Sesiones de Entrenamiento y Registro Rápido de Series (`/api/sesiones`)

### `POST /api/sesiones`
Inicia una nueva sesión de entrenamiento (libre o basada en una rutina).
- **Autenticación:** Requerida.
- **Request Body:**
```json
{
  "rutina_id": 10
}
```
- **Response `201 Created`:**
```json
{
  "id": 100,
  "usuario_id": 1,
  "rutina_id": 10,
  "estado": "ACTIVA",
  "fecha_inicio": "2026-10-25T19:30:00+00:00"
}
```
- **Errores:** `400 Bad Request`, `404 Not Found` (si `rutina_id` no pertenece al usuario).

### `GET /api/sesiones/<int:sesion_id>/ultimo-registro/<int:ejercicio_id>`
Obtiene el último peso y repeticiones usados por el usuario en un ejercicio para precargar los controles `+/-` sin usar el teclado.
- **Autenticación:** Requerida.
- **Response `200 OK`:**
```json
{
  "ejercicio_id": 1,
  "peso": 80.0,
  "repeticiones": 8,
  "tiene_historial": true
}
```
*(Si no existen series previas, retorna valores sugeridos por defecto: `peso: 20.0`, `repeticiones: 10`, `tiene_historial: false`).*

### `POST /api/sesiones/<int:sesion_id>/series`
Registra una serie en menos de 10 segundos y dispara el patrón `Observer` para evaluar si se ha batido un Récord Personal (PR).
- **Autenticación:** Requerida.
- **Request Body:**
```json
{
  "ejercicio_id": 1,
  "peso": 85.0,
  "repeticiones": 8
}
```
- **Response `201 Created`:**
```json
{
  "serie": {
    "id": 501,
    "sesion_id": 100,
    "ejercicio_id": 1,
    "peso": 85.0,
    "repeticiones": 8,
    "volumen": 680.0,
    "fecha_hora": "2026-10-25T19:35:10+00:00"
  },
  "nuevo_pr": true,
  "pr_detalle": {
    "id": 12,
    "tipo_pr": "PESO_MAXIMO",
    "peso": 85.0
  },
  "descanso_sugerido_segundos": 90
}
```
- **Errores:** `400 Bad Request` (sesión ya `FINALIZADA`, peso `< 0` o repeticiones `<= 0`), `403 Forbidden`, `404 Not Found`.

### `POST /api/sesiones/<int:sesion_id>/finalizar`
Transiciona el estado de la sesión de `ACTIVA` a `FINALIZADA` (vía patrón `State`).
- **Autenticación:** Requerida.
- **Response `200 OK`:**
```json
{
  "id": 100,
  "estado": "FINALIZADA",
  "fecha_inicio": "2026-10-25T19:30:00+00:00",
  "fecha_fin": "2026-10-25T20:15:00+00:00",
  "total_series": 16,
  "volumen_total": 9420.0
}
```
- **Errores:** `400 Bad Request` (si la sesión ya estaba finalizada), `403 Forbidden`, `404 Not Found`.

---

## 6. Historial, Progreso, Mapa Muscular y Resumen Mensual

### `GET /api/historial`
Lista las sesiones históricas del usuario con métricas resumidas.
- **Autenticación:** Requerida.
- **Query Params:** `limit` (default `20`), `offset` (default `0`).
- **Response `200 OK`:**
```json
{
  "sesiones": [
    {
      "id": 100,
      "rutina_nombre": "Empuje (Push)",
      "estado": "FINALIZADA",
      "fecha_inicio": "2026-10-25T19:30:00+00:00",
      "fecha_fin": "2026-10-25T20:15:00+00:00",
      "total_series": 16,
      "volumen_total": 9420.0
    }
  ]
}
```

### `GET /api/progreso/<int:ejercicio_id>`
Retorna las series temporales de peso máximo y volumen para renderizar gráficas en Chart.js.
- **Autenticación:** Requerida.
- **Response `200 OK`:**
```json
{
  "ejercicio_id": 1,
  "ejercicio_nombre": "Press de Banca con Barra",
  "puntos": [
    {
      "fecha": "2026-10-01",
      "peso_maximo": 80.0,
      "volumen_serie_max": 640.0,
      "repeticiones": 8
    },
    {
      "fecha": "2026-10-25",
      "peso_maximo": 85.0,
      "volumen_serie_max": 680.0,
      "repeticiones": 8
    }
  ],
  "pr_historico": 85.0
}
```
- **Errores:** `404 Not Found` (ejercicio inexistente o no visible).

### `GET /api/mapa-muscular`
Retorna la activación muscular acumulada (primaria vs. secundaria) en los últimos `dias` (default 7) para colorear la silueta SVG.
- **Autenticación:** Requerida.
- **Query Params:** `dias` (default `7`).
- **Response `200 OK`:**
```json
{
  "dias_ventana": 7,
  "grupos": [
    {
      "grupo_id": 1,
      "nombre": "Pecho",
      "series_primarias": 12,
      "series_secundarias": 0,
      "nivel_activacion": "PRIMARIO"
    },
    {
      "grupo_id": 4,
      "nombre": "Tríceps",
      "series_primarias": 0,
      "series_secundarias": 12,
      "nivel_activacion": "SECUNDARIO"
    }
  ]
}
```

### `GET /api/resumen-mensual`
Agrega las métricas de los últimos 30 días mediante `ResumenMensualFacade` y clasifica el desempeño del usuario.
- **Autenticación:** Requerida.
- **Query Params:** `dias` (default `30`).
- **Response `200 OK`:**
```json
{
  "ventana_dias": 30,
  "sesiones_completadas": 14,
  "total_series": 180,
  "volumen_total_kg": 86400.0,
  "nuevos_prs": 5,
  "grupo_mas_entrenado": "Pecho",
  "clasificacion": {
    "categoria": "Constante",
    "mensaje": "¡Excelente ritmo! Mantuviste una frecuencia sólida este mes."
  },
  "prs_detalle": [
    {
      "ejercicio_nombre": "Press de Banca con Barra",
      "peso": 85.0,
      "tipo_pr": "PESO_MAXIMO",
      "fecha": "2026-10-25T19:35:10+00:00"
    }
  ]
}
```
