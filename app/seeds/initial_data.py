"""Semillas iniciales idempotentes para grupos musculares, 40 ejercicios comerciales, 12 rutinas famosas y usuario demo."""

from sqlalchemy import inspect, text

from app import db
from app.patterns.factory import EjercicioFactory
from app.repositories.ejercicio_repository import EjercicioRepository
from app.repositories.rutina_repository import RutinaRepository
from app.repositories.usuario_repository import UsuarioRepository

DEMO_USER_EMAIL = "demo@fittracker.local"
DEMO_USER_PASSWORD = "FitTracker123!"
DEMO_USER_NOMBRE = "Atleta Demo"

GRUPOS_MUSCULARES_BASE: list[str] = [
    "Pecho",
    "Espalda",
    "Hombros",
    "Bíceps",
    "Tríceps",
    "Cuádriceps",
    "Isquiotibiales",
    "Glúteos",
    "Pantorrillas",
    "Core",
]

# Catálogo ampliado de 40 ejercicios predeterminados de gimnasio comercial en español
EJERCICIOS_PREDETERMINADOS_BASE: list[dict] = [
    {
        "nombre": "Press de banca con barra",
        "primarios": ["Pecho"],
        "secundarios": ["Tríceps", "Hombros"],
    },
    {
        "nombre": "Press inclinado con mancuernas",
        "primarios": ["Pecho"],
        "secundarios": ["Hombros", "Tríceps"],
    },
    {
        "nombre": "Aperturas en polea",
        "primarios": ["Pecho"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Aperturas en máquina Contractora / Pec Deck",
        "primarios": ["Pecho"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Press de pecho en máquina sentada",
        "primarios": ["Pecho"],
        "secundarios": ["Tríceps", "Hombros"],
    },
    {
        "nombre": "Fondos en paralelas",
        "primarios": ["Pecho", "Tríceps"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Fondos en máquina asistida o paralelas",
        "primarios": ["Pecho", "Tríceps"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Dominadas",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps", "Core"],
    },
    {
        "nombre": "Jalón al pecho en polea",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps"],
    },
    {
        "nombre": "Remo con barra",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps", "Isquiotibiales", "Core"],
    },
    {
        "nombre": "Remo en polea baja",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps", "Hombros"],
    },
    {
        "nombre": "Remo en polea baja (Gironda)",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps", "Hombros"],
    },
    {
        "nombre": "Pull-over en polea alta",
        "primarios": ["Espalda"],
        "secundarios": ["Pecho", "Tríceps", "Core"],
    },
    {
        "nombre": "Press militar",
        "primarios": ["Hombros"],
        "secundarios": ["Tríceps", "Core"],
    },
    {
        "nombre": "Press de hombros en máquina convergente",
        "primarios": ["Hombros"],
        "secundarios": ["Tríceps"],
    },
    {
        "nombre": "Elevaciones laterales",
        "primarios": ["Hombros"],
        "secundarios": [],
    },
    {
        "nombre": "Pájaros con mancuernas",
        "primarios": ["Hombros"],
        "secundarios": ["Espalda"],
    },
    {
        "nombre": "Elevaciones posteriores en máquina (Pájaros)",
        "primarios": ["Hombros"],
        "secundarios": ["Espalda"],
    },
    {
        "nombre": "Encogimientos de hombros con mancuernas",
        "primarios": ["Hombros", "Espalda"],
        "secundarios": [],
    },
    {
        "nombre": "Curl con barra",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Curl martillo con mancuernas",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Curl predicador en máquina o banco Scott",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Curl de bíceps en polea baja",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Extensión de tríceps en polea",
        "primarios": ["Tríceps"],
        "secundarios": [],
    },
    {
        "nombre": "Press francés con barra Z",
        "primarios": ["Tríceps"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Press francés / Rompecráneos",
        "primarios": ["Tríceps"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Sentadilla libre",
        "primarios": ["Cuádriceps", "Glúteos"],
        "secundarios": ["Isquiotibiales", "Core"],
    },
    {
        "nombre": "Sentadilla Hack en máquina",
        "primarios": ["Cuádriceps"],
        "secundarios": ["Glúteos"],
    },
    {
        "nombre": "Prensa de piernas",
        "primarios": ["Cuádriceps"],
        "secundarios": ["Glúteos", "Isquiotibiales"],
    },
    {
        "nombre": "Extensión de cuádriceps en máquina",
        "primarios": ["Cuádriceps"],
        "secundarios": [],
    },
    {
        "nombre": "Zancadas / Búlgaras con mancuernas",
        "primarios": ["Cuádriceps", "Glúteos"],
        "secundarios": ["Isquiotibiales", "Core"],
    },
    {
        "nombre": "Peso muerto rumano",
        "primarios": ["Isquiotibiales", "Glúteos"],
        "secundarios": ["Espalda", "Core"],
    },
    {
        "nombre": "Curl femoral tumbado",
        "primarios": ["Isquiotibiales"],
        "secundarios": ["Pantorrillas"],
    },
    {
        "nombre": "Hip thrust",
        "primarios": ["Glúteos"],
        "secundarios": ["Isquiotibiales", "Core"],
    },
    {
        "nombre": "Aducción/Abducción de cadera en máquina",
        "primarios": ["Glúteos"],
        "secundarios": ["Cuádriceps", "Isquiotibiales"],
    },
    {
        "nombre": "Elevación de talones de pie",
        "primarios": ["Pantorrillas"],
        "secundarios": [],
    },
    {
        "nombre": "Elevación de talones sentado en máquina (Sóleo)",
        "primarios": ["Pantorrillas"],
        "secundarios": [],
    },
    {
        "nombre": "Plancha abdominal",
        "primarios": ["Core"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Crunch abdominal en polea o máquina",
        "primarios": ["Core"],
        "secundarios": [],
    },
    {
        "nombre": "Elevación de piernas colgado",
        "primarios": ["Core"],
        "secundarios": ["Hombros"],
    },
]

# Catálogo oficial de las 12 Rutinas Famosas Inteligentes
RUTINAS_FAMOSAS_BASE: list[dict] = [
    {
        "nombre": "Full Body Sobrecarga (Ectomorfos / Hardgainers)",
        "descripcion": "Básicos multiarticulares pesados 3 días por semana para maximizar síntesis proteica sin gasto calórico excesivo.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "ECTOMORFO",
        "nivel": "PRINCIPIANTE",
        "dias_semana": "LUN,MIE,VIE",
        "descanso_segundos": 150,
        "ejercicios": [
            ("Sentadilla libre", 4),
            ("Press de banca con barra", 4),
            ("Remo con barra", 4),
            ("Press militar", 3),
            ("Curl con barra", 3),
        ],
    },
    {
        "nombre": "StrongLifts 5x5 Comercial (Fuerza y Masa Base)",
        "descripcion": "Progresión lineal clásica 5x5 en ejercicios compuestos para ganar densidad muscular y fuerza bruta.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "ECTOMORFO",
        "nivel": "INTERMEDIO",
        "dias_semana": "LUN,MIE,VIE",
        "descanso_segundos": 150,
        "ejercicios": [
            ("Sentadilla libre", 5),
            ("Press de banca con barra", 5),
            ("Remo con barra", 5),
            ("Press militar", 5),
            ("Peso muerto rumano", 3),
        ],
    },
    {
        "nombre": "Upper / Lower (Torso / Pierna Clásica)",
        "descripcion": "Frecuencia 2 óptima dividiendo tren superior e inferior en 4 sesiones equilibradas.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "INTERMEDIO",
        "dias_semana": "LUN,MAR,JUE,VIE",
        "descanso_segundos": 120,
        "ejercicios": [
            ("Press inclinado con mancuernas", 4),
            ("Jalón al pecho en polea", 4),
            ("Sentadilla Hack en máquina", 4),
            ("Peso muerto rumano", 3),
            ("Elevaciones laterales", 3),
        ],
    },
    {
        "nombre": "PHUL (Fuerza e Hipertrofia 4 Días)",
        "descripcion": "Power Hypertrophy Upper Lower: combina cargas pesadas de fuerza con bombeo en máquinas comerciales.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "AVANZADO",
        "dias_semana": "LUN,MAR,JUE,VIE",
        "descanso_segundos": 120,
        "ejercicios": [
            ("Press de banca con barra", 4),
            ("Remo en polea baja (Gironda)", 4),
            ("Prensa de piernas", 4),
            ("Curl femoral tumbado", 3),
            ("Curl predicador en máquina o banco Scott", 3),
            ("Press francés / Rompecráneos", 3),
        ],
    },
    {
        "nombre": "Push / Pull / Legs (Empuje, Tirón y Pierna)",
        "descripcion": "La división reina de hipertrofia moderna agrupando músculos sinérgicos con alto volumen semanal.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "INTERMEDIO",
        "dias_semana": "LUN,MAR,MIE,JUE,VIE,SAB",
        "descanso_segundos": 90,
        "ejercicios": [
            ("Press de pecho en máquina sentada", 4),
            ("Aperturas en máquina Contractora / Pec Deck", 3),
            ("Dominadas", 4),
            ("Pull-over en polea alta", 3),
            ("Sentadilla Hack en máquina", 4),
            ("Extensión de tríceps en polea", 3),
        ],
    },
    {
        "nombre": "Arnold Split Clásico (Pecho-Espalda / Brazo / Pierna)",
        "descripcion": "Antagonistas en superserie (Pecho y Espalda) y día dedicado a Hombros y Brazos estilo Golden Era.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "AVANZADO",
        "dias_semana": "LUN,MAR,MIE,JUE,VIE",
        "descanso_segundos": 90,
        "ejercicios": [
            ("Press inclinado con mancuernas", 4),
            ("Dominadas", 4),
            ("Press militar", 4),
            ("Curl con barra", 3),
            ("Press francés con barra Z", 3),
            ("Sentadilla libre", 4),
        ],
    },
    {
        "nombre": "Bro Split Comercial en Máquinas (1 Grupo por Día)",
        "descripcion": "Aislamiento guiado en máquinas de gimnasio comercial para congestionar cada músculo con máxima seguridad.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "TODOS",
        "nivel": "PRINCIPIANTE",
        "dias_semana": "LUN,MAR,MIE,JUE,VIE",
        "descanso_segundos": 90,
        "ejercicios": [
            ("Press de pecho en máquina sentada", 4),
            ("Jalón al pecho en polea", 4),
            ("Press de hombros en máquina convergente", 4),
            ("Prensa de piernas", 4),
            ("Curl predicador en máquina o banco Scott", 3),
            ("Extensión de tríceps en polea", 3),
        ],
    },
    {
        "nombre": "Quema Grasa Metabólica & Fuerza (Endomorfos)",
        "descripcion": "Alta densidad de trabajo con descansos cortos (60s) y grandes grupos musculares para elevar el gasto calórico.",
        "meta_objetivo": "BAJAR_PESO",
        "somatotipo_ideal": "ENDOMORFO",
        "nivel": "INTERMEDIO",
        "dias_semana": "LUN,MAR,JUE,VIE",
        "descanso_segundos": 60,
        "ejercicios": [
            ("Prensa de piernas", 4),
            ("Press inclinado con mancuernas", 4),
            ("Remo en polea baja (Gironda)", 4),
            ("Zancadas / Búlgaras con mancuernas", 3),
            ("Crunch abdominal en polea o máquina", 3),
        ],
    },
    {
        "nombre": "Circuito Full Body Recomposición (Cero Impacto)",
        "descripcion": "Estaciones guiadas sin impacto articular con transiciones de 60s ideales para pérdida de grasa sostenible.",
        "meta_objetivo": "BAJAR_PESO",
        "somatotipo_ideal": "ENDOMORFO",
        "nivel": "PRINCIPIANTE",
        "dias_semana": "LUN,MIE,VIE",
        "descanso_segundos": 60,
        "ejercicios": [
            ("Press de pecho en máquina sentada", 3),
            ("Jalón al pecho en polea", 3),
            ("Extensión de cuádriceps en máquina", 3),
            ("Curl femoral tumbado", 3),
            ("Plancha abdominal", 3),
        ],
    },
    {
        "nombre": "Definición Atlética & Densidad (Shred PPL)",
        "descripcion": "Volumen alto con descansos estrictos de 60s para preservar masa magra y maximizar definición muscular.",
        "meta_objetivo": "DEFINIR",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "INTERMEDIO",
        "dias_semana": "LUN,MAR,JUE,VIE,SAB",
        "descanso_segundos": 60,
        "ejercicios": [
            ("Fondos en máquina asistida o paralelas", 4),
            ("Aperturas en polea", 3),
            ("Pull-over en polea alta", 4),
            ("Elevaciones posteriores en máquina (Pájaros)", 3),
            ("Sentadilla Hack en máquina", 4),
            ("Elevación de piernas colgado", 3),
        ],
    },
    {
        "nombre": "Torso / Pierna Definición Estética",
        "descripcion": "Énfasis en proporciones en V (hombros laterales, dorsal ancho y abdomen) manteniendo cargas pesadas.",
        "meta_objetivo": "DEFINIR",
        "somatotipo_ideal": "ECTOMORFO",
        "nivel": "INTERMEDIO",
        "dias_semana": "LUN,MAR,JUE,VIE",
        "descanso_segundos": 75,
        "ejercicios": [
            ("Press inclinado con mancuernas", 4),
            ("Dominadas", 4),
            ("Elevaciones laterales", 4),
            ("Prensa de piernas", 4),
            ("Curl martillo con mancuernas", 3),
            ("Crunch abdominal en polea o máquina", 3),
        ],
    },
    {
        "nombre": "Glúteo & Pierna Prioridad + Torso (Strong Curves)",
        "descripcion": "Prioriza cadena posterior (Hip Thrust, Búlgaras, Abducción y Rumano) con tonificación estilizada de torso.",
        "meta_objetivo": "DEFINIR",
        "somatotipo_ideal": "TODOS",
        "nivel": "INTERMEDIO",
        "dias_semana": "LUN,MAR,JUE,VIE",
        "descanso_segundos": 90,
        "ejercicios": [
            ("Hip thrust", 4),
            ("Zancadas / Búlgaras con mancuernas", 4),
            ("Peso muerto rumano", 4),
            ("Aducción/Abducción de cadera en máquina", 3),
            ("Jalón al pecho en polea", 3),
            ("Elevaciones laterales", 3),
        ],
    },
]


def _asegurar_esquema_actualizado() -> None:
    """Asegura que tablas y nuevas columnas de OTP/PerfilUsuario/Rutinas Famosas existan en SQLite local."""
    inspector = inspect(db.engine)
    tablas = set(inspector.get_table_names())
    if "rutinas" in tablas:
        columnas_rutinas = {c["name"]: c for c in inspector.get_columns("rutinas")}
        if (
            "es_plantilla_famosa" not in columnas_rutinas
            or not columnas_rutinas.get("usuario_id", {}).get("nullable", True)
        ):
            db.drop_all()
            db.create_all()
            return

    if "usuarios" in tablas:
        columnas_usuarios = {c["name"] for c in inspector.get_columns("usuarios")}
        if "email_verificado" not in columnas_usuarios:
            db.session.execute(
                text("ALTER TABLE usuarios ADD COLUMN email_verificado BOOLEAN NOT NULL DEFAULT 0")
            )
        if "codigo_verificacion" not in columnas_usuarios:
            db.session.execute(
                text("ALTER TABLE usuarios ADD COLUMN codigo_verificacion VARCHAR(6)")
            )
        if "codigo_expiracion" not in columnas_usuarios:
            db.session.execute(
                text("ALTER TABLE usuarios ADD COLUMN codigo_expiracion DATETIME")
            )
        db.session.commit()
    db.create_all()


def seed_database(incluir_demo: bool = True) -> dict:
    """Crea tablas si no existen y puebla de forma idempotente grupos, 40 ejercicios, 12 rutinas famosas y demo."""
    _asegurar_esquema_actualizado()

    repo = EjercicioRepository()
    rutina_repo = RutinaRepository()
    usuario_repo = UsuarioRepository()

    grupos_existentes = {g.nombre: g for g in repo.listar_grupos_musculares()}
    grupos_creados = 0

    for nombre_grupo in GRUPOS_MUSCULARES_BASE:
        if nombre_grupo not in grupos_existentes:
            nuevo_grupo = repo.crear_grupo_muscular(nombre_grupo)
            grupos_existentes[nombre_grupo] = nuevo_grupo
            grupos_creados += 1

    # Para ejercicios predeterminados usamos usuario_id=0 (solo devuelve es_predeterminado=True)
    ejercicios_existentes = {
        e.nombre.lower(): e
        for e in repo.buscar_visibles_para_usuario(usuario_id=0)
        if e.es_predeterminado
    }
    ejercicios_creados = 0

    for item in EJERCICIOS_PREDETERMINADOS_BASE:
        clave = item["nombre"].strip().lower()
        if clave not in ejercicios_existentes:
            primarios_ids = [grupos_existentes[g].id for g in item["primarios"]]
            secundarios_ids = [grupos_existentes[g].id for g in item["secundarios"]]
            datos = EjercicioFactory.crear_predeterminado(
                nombre=item["nombre"],
                grupos_primarios_ids=primarios_ids,
                grupos_secundarios_ids=secundarios_ids,
            )
            nuevo_ej = repo.crear_ejercicio(
                nombre=datos["nombre"],
                es_predeterminado=datos["es_predeterminado"],
                creado_por=datos["creado_por"],
                grupos_primarios_ids=datos["grupos_primarios_ids"],
                grupos_secundarios_ids=datos["grupos_secundarios_ids"],
            )
            ejercicios_existentes[clave] = nuevo_ej
            ejercicios_creados += 1

    # Poblar de forma idempotente el catálogo de las 12 Rutinas Famosas
    plantillas_existentes = {
        r.nombre.strip().lower(): r for r in rutina_repo.listar_plantillas_famosas()
    }
    rutinas_famosas_creadas = 0

    for plantilla_def in RUTINAS_FAMOSAS_BASE:
        clave_rutina = plantilla_def["nombre"].strip().lower()
        if clave_rutina not in plantillas_existentes:
            items_ejercicios = []
            for orden_idx, (nombre_ej, series_obj) in enumerate(plantilla_def["ejercicios"], start=1):
                ej_obj = ejercicios_existentes.get(nombre_ej.strip().lower())
                if ej_obj is not None:
                    items_ejercicios.append(
                        {
                            "ejercicio_id": ej_obj.id,
                            "orden": orden_idx,
                            "descanso_segundos": plantilla_def["descanso_segundos"],
                            "series_objetivo": series_obj,
                        }
                    )
            if items_ejercicios:
                nueva_plantilla = rutina_repo.crear(
                    usuario_id=None,
                    nombre=plantilla_def["nombre"],
                    es_favorita=False,
                    ejercicios_items=items_ejercicios,
                    es_plantilla_famosa=True,
                    descripcion=plantilla_def["descripcion"],
                    meta_objetivo=plantilla_def["meta_objetivo"],
                    somatotipo_ideal=plantilla_def["somatotipo_ideal"],
                    nivel=plantilla_def["nivel"],
                    dias_semana=plantilla_def["dias_semana"],
                )
                plantillas_existentes[clave_rutina] = nueva_plantilla
                rutinas_famosas_creadas += 1

    demo_creado = False
    if incluir_demo:
        existente_demo = usuario_repo.obtener_por_email(DEMO_USER_EMAIL)
        if existente_demo is None:
            existente_demo = usuario_repo.crear(
                nombre=DEMO_USER_NOMBRE,
                email=DEMO_USER_EMAIL,
                password=DEMO_USER_PASSWORD,
                email_verificado=True,
            )
            demo_creado = True
        elif not existente_demo.email_verificado:
            usuario_repo.marcar_email_verificado(existente_demo.id)

        usuario_repo.guardar_perfil_usuario(
            usuario_id=existente_demo.id,
            sexo="HOMBRE",
            peso_kg=75.0,
            porcentaje_grasa=15.0,
            meta="GANAR_MASA",
            somatotipo="MESOMORFO",
            onboarding_completado=True,
        )

    return {
        "grupos_creados": grupos_creados,
        "ejercicios_creados": ejercicios_creados,
        "rutinas_famosas_creadas": rutinas_famosas_creadas,
        "total_grupos": len(grupos_existentes),
        "total_ejercicios": len(ejercicios_existentes),
        "total_rutinas_famosas": len(plantillas_existentes),
        "demo_email": DEMO_USER_EMAIL if incluir_demo else None,
        "demo_creado": demo_creado,
    }
