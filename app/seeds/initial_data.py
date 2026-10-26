"""Semillas iniciales idempotentes para el catálogo de grupos musculares, ejercicios y usuario demo."""

from sqlalchemy import inspect, text

from app import db
from app.patterns.factory import EjercicioFactory
from app.repositories.ejercicio_repository import EjercicioRepository
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

# Catálogo base de 23 ejercicios predeterminados en español con músculos primarios y secundarios
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
        "nombre": "Fondos en paralelas",
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
        "nombre": "Press militar",
        "primarios": ["Hombros"],
        "secundarios": ["Tríceps", "Core"],
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
        "nombre": "Sentadilla libre",
        "primarios": ["Cuádriceps", "Glúteos"],
        "secundarios": ["Isquiotibiales", "Core"],
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
        "nombre": "Elevación de talones de pie",
        "primarios": ["Pantorrillas"],
        "secundarios": [],
    },
    {
        "nombre": "Plancha abdominal",
        "primarios": ["Core"],
        "secundarios": ["Hombros"],
    },
]


def _asegurar_esquema_actualizado() -> None:
    """Asegura que tablas y nuevas columnas de OTP/PerfilUsuario existan en SQLite local."""
    inspector = inspect(db.engine)
    tablas = set(inspector.get_table_names())
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
    """Crea tablas si no existen y puebla de forma idempotente grupos, ejercicios y usuario demo."""
    _asegurar_esquema_actualizado()

    repo = EjercicioRepository()
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
        "total_grupos": len(grupos_existentes),
        "total_ejercicios": len(ejercicios_existentes),
        "demo_email": DEMO_USER_EMAIL if incluir_demo else None,
        "demo_creado": demo_creado,
    }
