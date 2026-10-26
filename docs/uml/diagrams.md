# Diagramas UML y de Arquitectura — FitTracker Web App

Este documento presenta el modelado arquitectónico de **FitTracker Web App** utilizando sintaxis oficial **Mermaid**.

---

## 1. Diagrama de Casos de Uso (Flujo del Atleta)

```mermaid
flowchart LR
    Atleta["🏋️ Atleta (Usuario Autenticado)"]
    Visitante["👤 Visitante"]

    subgraph Auth["Módulo de Acceso"]
        UC1["RF-01: Registrarse"]
        UC2["RF-02: Iniciar / Cerrar Sesión"]
    end

    subgraph Catalog["Catálogo y Rutinas"]
        UC3["RF-04: Buscar Ejercicio en 0ms"]
        UC4["RF-07: Crear Ejercicio Personalizado al Vuelo"]
        UC5["RF-08/09: Crear Rutina y Marcar Favorita"]
    end

    subgraph Workout["Entrenamiento en < 10 Segundos"]
        UC6["RF-05/06: Registrar Serie con Botones +/-"]
        UC7["RF-10: Detectar y Celebrar Nuevo PR"]
        UC8["RF-12: Activar Cronómetro de Descanso"]
        UC9["RF-16: Finalizar Sesión"]
    end

    subgraph Analytics["Analítica y Resumen 30d"]
        UC10["RF-13: Visualizar Mapa Muscular SVG Bicolor"]
        UC11["RF-14: Consultar Gráfica de Progreso"]
        UC12["RF-15: Consultar Resumen Mensual (MEJORO / ESTANCADO)"]
    end

    Visitante --> UC1
    Visitante --> UC2
    Atleta --> UC3
    Atleta --> UC4
    Atleta --> UC5
    Atleta --> UC6
    UC6 --> UC7
    UC6 --> UC8
    Atleta --> UC9
    Atleta --> UC10
    Atleta --> UC11
    Atleta --> UC12
```

---

## 2. Diagrama de Clases UML (Modelos + 5 Patrones GoF)

```mermaid
classDiagram
    class Usuario {
        +int id
        +str nombre
        +str email
        +str password_hash
        +datetime fecha_registro
        +set_password(password)
        +check_password(password) bool
    }

    class Ejercicio {
        +int id
        +str nombre
        +bool es_predeterminado
        +int creado_por
    }

    class GrupoMuscular {
        +int id
        +str nombre
    }

    class EjercicioGrupo {
        +int id
        +int ejercicio_id
        +int grupo_muscular_id
        +bool es_primario
    }

    class Rutina {
        +int id
        +int usuario_id
        +str nombre
        +bool es_favorita
    }

    class Sesion {
        +int id
        +int usuario_id
        +int rutina_id
        +datetime fecha_inicio
        +datetime fecha_fin
        +str estado
    }

    class Serie {
        +int id
        +int sesion_id
        +int ejercicio_id
        +int numero_serie
        +float peso
        +int repeticiones
        +volumen() float
    }

    class PR {
        +int id
        +int usuario_id
        +int ejercicio_id
        +float peso
        +int repeticiones
        +str tipo_record
    }

    class EjercicioFactory {
        <<Factory Pattern>>
        +crear_predeterminado(nombre, primarios, secundarios)$ dict
        +crear_personalizado(nombre, usuario_id, primarios, secundarios)$ dict
    }

    class SesionState {
        <<State Pattern>>
        +validar_puede_agregar_serie(sesion)*
        +finalizar(sesion)* dict
    }

    class SesionActivaState {
        +validar_puede_agregar_serie(sesion)
        +finalizar(sesion) dict
    }

    class SesionFinalizadaState {
        +validar_puede_agregar_serie(sesion)
        +finalizar(sesion) dict
    }

    class PRStrategy {
        <<Strategy Pattern>>
        +es_nuevo_pr(peso, reps, max_peso, max_vol)* bool
    }

    class PesoMaximoStrategy {
        +es_nuevo_pr(peso, reps, max_peso, max_vol) bool
    }

    class VolumenSerieStrategy {
        +es_nuevo_pr(peso, reps, max_peso, max_vol) bool
    }

    class ComparacionMensualStrategy {
        <<Strategy Pattern>>
        +clasificar(sesiones_act, max_peso_act, max_vol_act, max_peso_prev, max_vol_prev) str
    }

    class SerieSubject {
        <<Observer Pattern>>
        +attach(observer)
        +notify(evento) list
    }

    class PRDetectionObserver {
        +update(evento) dict
    }

    class ResumenFacade {
        <<Facade Pattern>>
        +obtener_dashboard_mensual(usuario_id) dict
        +obtener_vista_mapa_muscular(usuario_id, dias) dict
        +obtener_vista_progreso_ejercicio(usuario_id, ejercicio_id) dict
    }

    Usuario "1" --> "*" Ejercicio : crea
    Usuario "1" --> "*" Rutina : posee
    Usuario "1" --> "*" Sesion : entrena
    Usuario "1" --> "*" PR : logra
    Ejercicio "1" --> "*" EjercicioGrupo : asocia
    GrupoMuscular "1" --> "*" EjercicioGrupo : clasifica
    Sesion "1" --> "*" Serie : contiene
    SesionState <|-- SesionActivaState
    SesionState <|-- SesionFinalizadaState
    PRStrategy <|-- PesoMaximoStrategy
    PRStrategy <|-- VolumenSerieStrategy
    SerieSubject --> PRDetectionObserver : notifica
    PRDetectionObserver --> PRStrategy : delega
    ResumenFacade --> ComparacionMensualStrategy : utiliza
```

---

## 3. Diagrama de Secuencia: Guardar Serie, Evaluación de PR y Cronómetro

```mermaid
sequenceDiagram
    actor Atleta
    participant UI as registro.js / cronometro.js
    participant API as sesion_controller.py
    participant Svc as SesionService
    participant State as SesionState
    participant Repo as SesionRepository
    participant Subj as SerieSubject
    participant Obs as PRDetectionObserver
    participant Strat as PesoMaximoStrategy
    participant PRSvc as PRService

    Atleta->>UI: Toca "¡SERIE TERMINADA!" (peso=75kg, reps=6)
    UI->>API: POST /api/sesiones/{id}/series
    API->>Svc: registrar_serie(usuario_id, sesion_id, ejercicio_id, 75.0, 6)
    Svc->>Repo: obtener_por_id_y_usuario(sesion_id, usuario_id)
    Repo-->>Svc: Sesion(estado="ACTIVA")
    Svc->>State: obtener_estado_sesion("ACTIVA").validar_puede_agregar_serie()
    State-->>Svc: OK
    Svc->>Repo: agregar_serie(sesion_id, ejercicio_id, numero_serie, 75.0, 6)
    Repo-->>Svc: Serie creada
    Svc->>Subj: notify({usuario_id, ejercicio_id, peso: 75.0, repeticiones: 6})
    Subj->>Obs: update(evento)
    Obs->>PRSvc: evaluar_y_registrar_pr(usuario_id, ejercicio_id, 75.0, 6)
    PRSvc->>Strat: es_nuevo_pr(75.0, 6, max_peso_historico=70.0)
    Strat-->>PRSvc: True
    PRSvc-->>Obs: {"es_pr": True, "nuevo_pr": PR(75.0kg)}
    Obs-->>Subj: resultado PR
    Svc-->>API: Payload serie + es_pr=True + descanso_segundos=150
    API-->>UI: 201 Created JSON
    par Inicio inmediato sin bloqueo
        UI->>UI: FitTrackerCronometro.iniciar(150)
    and Celebración Gamificada Duolingo
        UI->>UI: celebrarNuevoPR("Press Vikingo", 75.0) (Spring 380ms)
    end
```

---

## 4. Diagrama de Componentes y Arquitectura en Capas

```mermaid
flowchart TD
    subgraph Client["Frontend Mobile-First (Navegador Móvil <= 430px)"]
        Templates["Jinja2 Templates + Light Theme Duolingo (styles.css)"]
        JS["Módulos JS Vanilla (buscador.js, registro.js, cronometro.js, mapa.js, graficas.js)"]
        LocalStore["localStorage (Cola Offline + Timestamp Cronómetro)"]
        Templates --> JS
        JS <--> LocalStore
    end

    subgraph Controllers["Capa 1: Controladores Flask (app/controllers/)"]
        AuthBP["auth_bp"]
        EjBP["ejercicio_bp"]
        RutBP["rutina_bp"]
        SesBP["sesion_bp"]
        ResBP["resumen_bp"]
    end

    subgraph Domain["Capa 2 y 3: Servicios y Patrones GoF (app/services/ + app/patterns/)"]
        Services["AuthService | EjercicioService | RutinaService | SesionService | PRService | ResumenService"]
        Patterns["EjercicioFactory | SesionState | PRStrategy | ComparacionMensualStrategy | SerieSubject/Observer | ResumenFacade"]
        Services <--> Patterns
    end

    subgraph DataAccess["Capa 4: Repositorios SQLAlchemy (app/repositories/)"]
        Repos["UsuarioRepository | EjercicioRepository | RutinaRepository | SesionRepository | PRRepository"]
    end

    subgraph Persistence["Capa 5: Modelos y Motor SQLite WAL (app/models/)"]
        Models["9 Tablas SQLAlchemy + Índice Compuesto ix_pr_usuario_ejercicio_fecha"]
        SQLite[("SQLite 3 (journal_mode=WAL, foreign_keys=ON)")]
        Models --> SQLite
    end

    JS -->|fetch JSON /api/*| Controllers
    Controllers --> Domain
    Domain --> DataAccess
    DataAccess --> Persistence
```

