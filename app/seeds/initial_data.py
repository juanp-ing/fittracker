"""Semillas iniciales idempotentes para el catálogo de grupos musculares y ejercicios."""

from app.patterns.factory import EjercicioFactory
from app.repositories.ejercicio_repository import EjercicioRepository

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

# Catálogo base de 22 ejercicios predeterminados en español con músculos primarios y secundarios
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


def seed_database() -> dict:
    """Puebla de forma idempotente los grupos musculares y ejercicios predeterminados."""
    repo = EjercicioRepository()

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

    return {
        "grupos_creados": grupos_creados,
        "ejercicios_creados": ejercicios_creados,
        "total_grupos": len(grupos_existentes),
        "total_ejercicios": len(ejercicios_existentes),
    }
