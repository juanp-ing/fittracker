"""Semillas iniciales idempotentes: grupos musculares, catálogo de ejercicios, 12 rutinas famosas y usuario demo."""

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

# Catálogo de ejercicios predeterminados de gimnasio comercial en español
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
    # ---- Ampliación del catálogo (pesos libres, poleas y máquinas habituales) ----
    {
        "nombre": "Press de banca con mancuernas",
        "primarios": ["Pecho"],
        "secundarios": ["Tríceps", "Hombros"],
    },
    {
        "nombre": "Press inclinado con barra",
        "primarios": ["Pecho"],
        "secundarios": ["Hombros", "Tríceps"],
    },
    {
        "nombre": "Press declinado con barra",
        "primarios": ["Pecho"],
        "secundarios": ["Tríceps", "Hombros"],
    },
    {
        "nombre": "Press de banca en máquina Smith",
        "primarios": ["Pecho"],
        "secundarios": ["Tríceps", "Hombros"],
    },
    {
        "nombre": "Aperturas con mancuernas",
        "primarios": ["Pecho"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Cruce de poleas de arriba abajo",
        "primarios": ["Pecho"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Flexiones",
        "primarios": ["Pecho"],
        "secundarios": ["Tríceps", "Hombros", "Core"],
    },
    {
        "nombre": "Pull-over con mancuerna",
        "primarios": ["Pecho"],
        "secundarios": ["Espalda", "Tríceps"],
    },
    {
        "nombre": "Peso muerto convencional",
        "primarios": ["Espalda", "Isquiotibiales", "Glúteos"],
        "secundarios": ["Cuádriceps", "Core"],
    },
    {
        "nombre": "Dominadas supinas",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps"],
    },
    {
        "nombre": "Dominadas asistidas en máquina",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps"],
    },
    {
        "nombre": "Jalón al pecho con agarre cerrado",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps"],
    },
    {
        "nombre": "Remo con mancuerna a una mano",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps"],
    },
    {
        "nombre": "Remo en barra T",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps", "Core"],
    },
    {
        "nombre": "Remo en máquina sentado",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps"],
    },
    {
        "nombre": "Remo invertido en barra",
        "primarios": ["Espalda"],
        "secundarios": ["Bíceps", "Core"],
    },
    {
        "nombre": "Hiperextensiones lumbares",
        "primarios": ["Espalda"],
        "secundarios": ["Glúteos", "Isquiotibiales"],
    },
    {
        "nombre": "Encogimientos de hombros con barra",
        "primarios": ["Hombros", "Espalda"],
        "secundarios": [],
    },
    {
        "nombre": "Press militar con mancuernas sentado",
        "primarios": ["Hombros"],
        "secundarios": ["Tríceps"],
    },
    {
        "nombre": "Press Arnold",
        "primarios": ["Hombros"],
        "secundarios": ["Tríceps"],
    },
    {
        "nombre": "Elevaciones laterales en polea",
        "primarios": ["Hombros"],
        "secundarios": [],
    },
    {
        "nombre": "Elevaciones laterales en máquina",
        "primarios": ["Hombros"],
        "secundarios": [],
    },
    {
        "nombre": "Elevaciones frontales con mancuernas",
        "primarios": ["Hombros"],
        "secundarios": [],
    },
    {
        "nombre": "Remo al mentón con barra",
        "primarios": ["Hombros"],
        "secundarios": ["Espalda", "Bíceps"],
    },
    {
        "nombre": "Face pull en polea",
        "primarios": ["Hombros"],
        "secundarios": ["Espalda"],
    },
    {
        "nombre": "Curl con mancuernas alterno",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Curl inclinado con mancuernas",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Curl con barra Z",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Curl concentrado",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Curl inverso con barra",
        "primarios": ["Bíceps"],
        "secundarios": [],
    },
    {
        "nombre": "Press de banca con agarre cerrado",
        "primarios": ["Tríceps"],
        "secundarios": ["Pecho", "Hombros"],
    },
    {
        "nombre": "Extensión de tríceps sobre la cabeza en polea",
        "primarios": ["Tríceps"],
        "secundarios": [],
    },
    {
        "nombre": "Extensión de tríceps con mancuerna sobre la cabeza",
        "primarios": ["Tríceps"],
        "secundarios": [],
    },
    {
        "nombre": "Patada de tríceps con mancuerna",
        "primarios": ["Tríceps"],
        "secundarios": [],
    },
    {
        "nombre": "Fondos entre bancos",
        "primarios": ["Tríceps"],
        "secundarios": ["Pecho", "Hombros"],
    },
    {
        "nombre": "Sentadilla frontal",
        "primarios": ["Cuádriceps"],
        "secundarios": ["Glúteos", "Core"],
    },
    {
        "nombre": "Sentadilla en máquina Smith",
        "primarios": ["Cuádriceps"],
        "secundarios": ["Glúteos", "Isquiotibiales"],
    },
    {
        "nombre": "Sentadilla goblet",
        "primarios": ["Cuádriceps"],
        "secundarios": ["Glúteos", "Core"],
    },
    {
        "nombre": "Zancadas caminando con mancuernas",
        "primarios": ["Cuádriceps", "Glúteos"],
        "secundarios": ["Isquiotibiales"],
    },
    {
        "nombre": "Zancadas con barra",
        "primarios": ["Cuádriceps", "Glúteos"],
        "secundarios": ["Isquiotibiales"],
    },
    {
        "nombre": "Subida al cajón (step-up)",
        "primarios": ["Cuádriceps", "Glúteos"],
        "secundarios": [],
    },
    {
        "nombre": "Curl femoral sentado",
        "primarios": ["Isquiotibiales"],
        "secundarios": [],
    },
    {
        "nombre": "Peso muerto con piernas rígidas",
        "primarios": ["Isquiotibiales"],
        "secundarios": ["Glúteos", "Espalda"],
    },
    {
        "nombre": "Peso muerto rumano con mancuernas",
        "primarios": ["Isquiotibiales", "Glúteos"],
        "secundarios": ["Espalda"],
    },
    {
        "nombre": "Buenos días con barra",
        "primarios": ["Isquiotibiales"],
        "secundarios": ["Glúteos", "Espalda"],
    },
    {
        "nombre": "Curl nórdico",
        "primarios": ["Isquiotibiales"],
        "secundarios": ["Glúteos"],
    },
    {
        "nombre": "Hip thrust en máquina",
        "primarios": ["Glúteos"],
        "secundarios": ["Isquiotibiales"],
    },
    {
        "nombre": "Puente de glúteos",
        "primarios": ["Glúteos"],
        "secundarios": ["Isquiotibiales"],
    },
    {
        "nombre": "Patada de glúteo en polea",
        "primarios": ["Glúteos"],
        "secundarios": [],
    },
    {
        "nombre": "Patada de glúteo en máquina",
        "primarios": ["Glúteos"],
        "secundarios": [],
    },
    {
        "nombre": "Peso muerto sumo",
        "primarios": ["Glúteos", "Cuádriceps"],
        "secundarios": ["Isquiotibiales", "Espalda"],
    },
    {
        "nombre": "Sentadilla sumo con mancuerna",
        "primarios": ["Glúteos", "Cuádriceps"],
        "secundarios": [],
    },
    {
        "nombre": "Pull-through en polea",
        "primarios": ["Glúteos"],
        "secundarios": ["Isquiotibiales"],
    },
    {
        "nombre": "Balanceo con pesa rusa (kettlebell swing)",
        "primarios": ["Glúteos", "Isquiotibiales"],
        "secundarios": ["Core", "Hombros"],
    },
    {
        "nombre": "Elevación de talones en prensa",
        "primarios": ["Pantorrillas"],
        "secundarios": [],
    },
    {
        "nombre": "Elevación de talones a una pierna con mancuerna",
        "primarios": ["Pantorrillas"],
        "secundarios": [],
    },
    {
        "nombre": "Rueda abdominal",
        "primarios": ["Core"],
        "secundarios": [],
    },
    {
        "nombre": "Crunch abdominal en el suelo",
        "primarios": ["Core"],
        "secundarios": [],
    },
    {
        "nombre": "Elevación de piernas tumbado",
        "primarios": ["Core"],
        "secundarios": [],
    },
    {
        "nombre": "Elevación de rodillas en silla romana",
        "primarios": ["Core"],
        "secundarios": [],
    },
    {
        "nombre": "Giro ruso",
        "primarios": ["Core"],
        "secundarios": [],
    },
    {
        "nombre": "Plancha lateral",
        "primarios": ["Core"],
        "secundarios": [],
    },
    {
        "nombre": "Leñador en polea",
        "primarios": ["Core"],
        "secundarios": ["Hombros"],
    },
    {
        "nombre": "Paseo del granjero",
        "primarios": ["Core"],
        "secundarios": ["Hombros", "Espalda"],
    },
]

# Catálogo oficial de las 12 Rutinas Famosas. Cada una define el plan real de cada día:
# «dias» lista (código, nombre del día, [(ejercicio, series)]) y de ahí sale «dias_semana».
RUTINAS_FAMOSAS_BASE: list[dict] = [
    {
        "nombre": "Full Body Sobrecarga (Ectomorfos / Hardgainers)",
        "descripcion": "Tres entrenamientos de cuerpo completo distintos por semana, con básicos pesados y un día de descanso entre ellos.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "ECTOMORFO",
        "nivel": "PRINCIPIANTE",
        "descanso_segundos": 120,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Cuerpo completo A",
                "ejercicios": [
                    ("Sentadilla libre", 4),
                    ("Press de banca con barra", 4),
                    ("Remo con barra", 4),
                    ("Press militar", 3),
                    ("Curl con barra", 3),
                    ("Plancha abdominal", 3),
                ],
            },
            {
                "dia": "MIE",
                "nombre": "Cuerpo completo B",
                "ejercicios": [
                    ("Peso muerto convencional", 3),
                    ("Press inclinado con mancuernas", 4),
                    ("Dominadas", 4),
                    ("Zancadas caminando con mancuernas", 3),
                    ("Extensión de tríceps en polea", 3),
                    ("Elevación de talones de pie", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Cuerpo completo C",
                "ejercicios": [
                    ("Prensa de piernas", 4),
                    ("Press militar con mancuernas sentado", 4),
                    ("Jalón al pecho en polea", 4),
                    ("Peso muerto rumano", 3),
                    ("Fondos en paralelas", 3),
                    ("Curl martillo con mancuernas", 3),
                ],
            },
        ],
    },
    {
        "nombre": "StrongLifts 5x5 Comercial (Fuerza y Masa Base)",
        "descripcion": "El 5x5 original: dos entrenamientos (A y B) que se alternan, con 5 series de 5 repeticiones y un poco más de peso en cada sesión.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "ECTOMORFO",
        "nivel": "INTERMEDIO",
        "descanso_segundos": 180,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Entrenamiento A",
                "ejercicios": [
                    ("Sentadilla libre", 5),
                    ("Press de banca con barra", 5),
                    ("Remo con barra", 5),
                ],
            },
            {
                "dia": "MIE",
                "nombre": "Entrenamiento B",
                "ejercicios": [
                    ("Sentadilla libre", 5),
                    ("Press militar", 5),
                    ("Peso muerto convencional", 1),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Entrenamiento A",
                "ejercicios": [
                    ("Sentadilla libre", 5),
                    ("Press de banca con barra", 5),
                    ("Remo con barra", 5),
                ],
            },
        ],
    },
    {
        "nombre": "Upper / Lower (Torso / Pierna Clásica)",
        "descripcion": "Cuatro días: dos de torso y dos de pierna, uno más pesado y otro con más volumen, para trabajar cada músculo dos veces por semana.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "INTERMEDIO",
        "descanso_segundos": 120,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Torso A",
                "ejercicios": [
                    ("Press de banca con barra", 4),
                    ("Remo con barra", 4),
                    ("Press militar", 3),
                    ("Jalón al pecho en polea", 3),
                    ("Curl con barra", 3),
                    ("Press francés con barra Z", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Pierna A",
                "ejercicios": [
                    ("Sentadilla libre", 4),
                    ("Peso muerto rumano", 4),
                    ("Prensa de piernas", 3),
                    ("Curl femoral tumbado", 3),
                    ("Elevación de talones de pie", 4),
                    ("Plancha abdominal", 3),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Torso B",
                "ejercicios": [
                    ("Press inclinado con mancuernas", 4),
                    ("Remo en polea baja", 4),
                    ("Press militar con mancuernas sentado", 3),
                    ("Dominadas", 3),
                    ("Elevaciones laterales", 3),
                    ("Curl martillo con mancuernas", 3),
                    ("Extensión de tríceps en polea", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Pierna B",
                "ejercicios": [
                    ("Peso muerto convencional", 3),
                    ("Sentadilla Hack en máquina", 4),
                    ("Zancadas caminando con mancuernas", 3),
                    ("Extensión de cuádriceps en máquina", 3),
                    ("Curl femoral sentado", 3),
                    ("Elevación de talones sentado en máquina (Sóleo)", 4),
                ],
            },
        ],
    },
    {
        "nombre": "PHUL (Fuerza e Hipertrofia 4 Días)",
        "descripcion": "Power Hypertrophy Upper Lower: dos días de fuerza con cargas pesadas y dos de hipertrofia con más repeticiones.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "AVANZADO",
        "descanso_segundos": 120,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Torso · fuerza",
                "ejercicios": [
                    ("Press de banca con barra", 4),
                    ("Press inclinado con mancuernas", 4),
                    ("Remo con barra", 4),
                    ("Jalón al pecho en polea", 4),
                    ("Press militar", 3),
                    ("Curl con barra", 3),
                    ("Press francés / Rompecráneos", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Pierna · fuerza",
                "ejercicios": [
                    ("Sentadilla libre", 4),
                    ("Peso muerto convencional", 4),
                    ("Prensa de piernas", 4),
                    ("Curl femoral tumbado", 4),
                    ("Elevación de talones de pie", 4),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Torso · hipertrofia",
                "ejercicios": [
                    ("Press inclinado con barra", 4),
                    ("Aperturas con mancuernas", 4),
                    ("Remo en polea baja", 4),
                    ("Remo con mancuerna a una mano", 4),
                    ("Elevaciones laterales", 4),
                    ("Curl inclinado con mancuernas", 4),
                    ("Extensión de tríceps en polea", 4),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Pierna · hipertrofia",
                "ejercicios": [
                    ("Sentadilla frontal", 4),
                    ("Zancadas con barra", 4),
                    ("Extensión de cuádriceps en máquina", 4),
                    ("Curl femoral sentado", 4),
                    ("Elevación de talones sentado en máquina (Sóleo)", 4),
                    ("Elevación de talones en prensa", 4),
                ],
            },
        ],
    },
    {
        "nombre": "Push / Pull / Legs (Empuje, Tirón y Pierna)",
        "descripcion": "Seis días: empuje (pecho, hombro y tríceps), tirón (espalda y bíceps) y pierna, dos vueltas por semana con ejercicios distintos en cada una.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "INTERMEDIO",
        "descanso_segundos": 90,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Empuje A",
                "ejercicios": [
                    ("Press de banca con barra", 4),
                    ("Press militar", 3),
                    ("Press inclinado con mancuernas", 3),
                    ("Elevaciones laterales", 3),
                    ("Extensión de tríceps en polea", 3),
                    ("Extensión de tríceps sobre la cabeza en polea", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Tirón A",
                "ejercicios": [
                    ("Peso muerto convencional", 3),
                    ("Dominadas", 3),
                    ("Remo en polea baja", 3),
                    ("Face pull en polea", 3),
                    ("Curl con barra", 4),
                    ("Curl martillo con mancuernas", 3),
                ],
            },
            {
                "dia": "MIE",
                "nombre": "Pierna A",
                "ejercicios": [
                    ("Sentadilla libre", 4),
                    ("Peso muerto rumano", 3),
                    ("Prensa de piernas", 3),
                    ("Curl femoral tumbado", 3),
                    ("Elevación de talones de pie", 4),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Empuje B",
                "ejercicios": [
                    ("Press militar con mancuernas sentado", 4),
                    ("Press inclinado con barra", 3),
                    ("Aperturas en máquina Contractora / Pec Deck", 3),
                    ("Elevaciones laterales en polea", 3),
                    ("Fondos en paralelas", 3),
                    ("Press francés con barra Z", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Tirón B",
                "ejercicios": [
                    ("Remo con barra", 4),
                    ("Jalón al pecho en polea", 3),
                    ("Remo con mancuerna a una mano", 3),
                    ("Pájaros con mancuernas", 3),
                    ("Curl con barra Z", 3),
                    ("Curl inclinado con mancuernas", 3),
                ],
            },
            {
                "dia": "SAB",
                "nombre": "Pierna B",
                "ejercicios": [
                    ("Sentadilla frontal", 4),
                    ("Hip thrust", 3),
                    ("Zancadas / Búlgaras con mancuernas", 3),
                    ("Extensión de cuádriceps en máquina", 3),
                    ("Curl femoral sentado", 3),
                    ("Elevación de talones sentado en máquina (Sóleo)", 4),
                ],
            },
        ],
    },
    {
        "nombre": "Arnold Split Clásico (Pecho-Espalda / Brazo / Pierna)",
        "descripcion": "La división de seis días de Arnold: pecho con espalda, hombros con brazos y pierna, dos vueltas por semana.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "AVANZADO",
        "descanso_segundos": 90,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Pecho y espalda A",
                "ejercicios": [
                    ("Press de banca con barra", 4),
                    ("Press inclinado con barra", 4),
                    ("Pull-over con mancuerna", 3),
                    ("Dominadas", 4),
                    ("Remo con barra", 4),
                    ("Peso muerto convencional", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Hombros y brazos A",
                "ejercicios": [
                    ("Press militar", 4),
                    ("Elevaciones laterales", 4),
                    ("Remo al mentón con barra", 3),
                    ("Curl con barra", 4),
                    ("Curl inclinado con mancuernas", 3),
                    ("Press de banca con agarre cerrado", 4),
                    ("Extensión de tríceps con mancuerna sobre la cabeza", 3),
                ],
            },
            {
                "dia": "MIE",
                "nombre": "Pierna A",
                "ejercicios": [
                    ("Sentadilla libre", 4),
                    ("Zancadas con barra", 4),
                    ("Curl femoral tumbado", 4),
                    ("Peso muerto con piernas rígidas", 3),
                    ("Elevación de talones de pie", 4),
                    ("Elevación de piernas colgado", 3),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Pecho y espalda B",
                "ejercicios": [
                    ("Press inclinado con mancuernas", 4),
                    ("Aperturas con mancuernas", 3),
                    ("Fondos en paralelas", 3),
                    ("Jalón al pecho en polea", 4),
                    ("Remo en barra T", 4),
                    ("Remo en polea baja", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Hombros y brazos B",
                "ejercicios": [
                    ("Press Arnold", 4),
                    ("Pájaros con mancuernas", 3),
                    ("Elevaciones laterales en polea", 3),
                    ("Curl con mancuernas alterno", 3),
                    ("Curl concentrado", 3),
                    ("Press francés con barra Z", 3),
                    ("Extensión de tríceps en polea", 3),
                ],
            },
            {
                "dia": "SAB",
                "nombre": "Pierna B",
                "ejercicios": [
                    ("Sentadilla frontal", 4),
                    ("Prensa de piernas", 4),
                    ("Extensión de cuádriceps en máquina", 3),
                    ("Curl femoral sentado", 3),
                    ("Buenos días con barra", 3),
                    ("Elevación de talones sentado en máquina (Sóleo)", 4),
                    ("Crunch abdominal en polea o máquina", 3),
                ],
            },
        ],
    },
    {
        "nombre": "Bro Split Comercial en Máquinas (1 Grupo por Día)",
        "descripcion": "Un grupo muscular por día, casi todo en máquinas guiadas: fácil de aprender y con una semana entera para recuperar cada músculo.",
        "meta_objetivo": "GANAR_MASA",
        "somatotipo_ideal": "TODOS",
        "nivel": "PRINCIPIANTE",
        "descanso_segundos": 90,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Pecho",
                "ejercicios": [
                    ("Press de pecho en máquina sentada", 4),
                    ("Press inclinado con mancuernas", 3),
                    ("Aperturas en máquina Contractora / Pec Deck", 3),
                    ("Cruce de poleas de arriba abajo", 3),
                    ("Fondos en máquina asistida o paralelas", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Espalda",
                "ejercicios": [
                    ("Jalón al pecho en polea", 4),
                    ("Remo en máquina sentado", 4),
                    ("Remo en polea baja (Gironda)", 3),
                    ("Pull-over en polea alta", 3),
                    ("Hiperextensiones lumbares", 3),
                ],
            },
            {
                "dia": "MIE",
                "nombre": "Hombros",
                "ejercicios": [
                    ("Press de hombros en máquina convergente", 4),
                    ("Elevaciones laterales en máquina", 4),
                    ("Elevaciones posteriores en máquina (Pájaros)", 3),
                    ("Elevaciones frontales con mancuernas", 3),
                    ("Encogimientos de hombros con mancuernas", 3),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Pierna",
                "ejercicios": [
                    ("Prensa de piernas", 4),
                    ("Sentadilla Hack en máquina", 3),
                    ("Extensión de cuádriceps en máquina", 3),
                    ("Curl femoral sentado", 3),
                    ("Aducción/Abducción de cadera en máquina", 3),
                    ("Elevación de talones sentado en máquina (Sóleo)", 4),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Brazos y abdomen",
                "ejercicios": [
                    ("Curl predicador en máquina o banco Scott", 4),
                    ("Curl de bíceps en polea baja", 3),
                    ("Curl martillo con mancuernas", 3),
                    ("Extensión de tríceps en polea", 4),
                    ("Extensión de tríceps sobre la cabeza en polea", 3),
                    ("Crunch abdominal en polea o máquina", 3),
                ],
            },
        ],
    },
    {
        "nombre": "Quema Grasa Metabólica & Fuerza (Endomorfos)",
        "descripcion": "Cuatro días con descansos cortos de 60 s y grandes grupos musculares para gastar más energía sin perder fuerza.",
        "meta_objetivo": "BAJAR_PESO",
        "somatotipo_ideal": "ENDOMORFO",
        "nivel": "INTERMEDIO",
        "descanso_segundos": 60,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Pierna y core",
                "ejercicios": [
                    ("Sentadilla goblet", 4),
                    ("Prensa de piernas", 4),
                    ("Zancadas caminando con mancuernas", 3),
                    ("Balanceo con pesa rusa (kettlebell swing)", 3),
                    ("Plancha abdominal", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Torso",
                "ejercicios": [
                    ("Press inclinado con mancuernas", 4),
                    ("Remo en polea baja (Gironda)", 4),
                    ("Press militar con mancuernas sentado", 3),
                    ("Jalón al pecho en polea", 3),
                    ("Flexiones", 3),
                    ("Crunch abdominal en polea o máquina", 3),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Glúteo y femoral",
                "ejercicios": [
                    ("Peso muerto rumano", 4),
                    ("Hip thrust", 4),
                    ("Curl femoral tumbado", 3),
                    ("Zancadas / Búlgaras con mancuernas", 3),
                    ("Paseo del granjero", 3),
                    ("Elevación de piernas tumbado", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Cuerpo completo en circuito",
                "ejercicios": [
                    ("Sentadilla Hack en máquina", 3),
                    ("Press de pecho en máquina sentada", 3),
                    ("Remo en máquina sentado", 3),
                    ("Press de hombros en máquina convergente", 3),
                    ("Balanceo con pesa rusa (kettlebell swing)", 3),
                    ("Giro ruso", 3),
                ],
            },
        ],
    },
    {
        "nombre": "Circuito Full Body Recomposición (Cero Impacto)",
        "descripcion": "Tres circuitos distintos de cuerpo completo en máquinas, sin saltos ni impacto, con 60 s entre estaciones.",
        "meta_objetivo": "BAJAR_PESO",
        "somatotipo_ideal": "ENDOMORFO",
        "nivel": "PRINCIPIANTE",
        "descanso_segundos": 60,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Circuito A",
                "ejercicios": [
                    ("Prensa de piernas", 3),
                    ("Press de pecho en máquina sentada", 3),
                    ("Jalón al pecho en polea", 3),
                    ("Curl femoral sentado", 3),
                    ("Press de hombros en máquina convergente", 3),
                    ("Plancha abdominal", 3),
                ],
            },
            {
                "dia": "MIE",
                "nombre": "Circuito B",
                "ejercicios": [
                    ("Sentadilla goblet", 3),
                    ("Remo en máquina sentado", 3),
                    ("Aperturas en máquina Contractora / Pec Deck", 3),
                    ("Extensión de cuádriceps en máquina", 3),
                    ("Elevaciones laterales en máquina", 3),
                    ("Crunch abdominal en polea o máquina", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Circuito C",
                "ejercicios": [
                    ("Sentadilla Hack en máquina", 3),
                    ("Dominadas asistidas en máquina", 3),
                    ("Press inclinado con mancuernas", 3),
                    ("Curl femoral tumbado", 3),
                    ("Curl de bíceps en polea baja", 3),
                    ("Extensión de tríceps en polea", 3),
                    ("Plancha lateral", 3),
                ],
            },
        ],
    },
    {
        "nombre": "Definición Atlética & Densidad (Shred PPL)",
        "descripcion": "Cinco días: empuje, tirón y pierna, más un día de torso y otro de pierna y glúteo, con descansos de 60 s para mantener el músculo mientras defines.",
        "meta_objetivo": "DEFINIR",
        "somatotipo_ideal": "MESOMORFO",
        "nivel": "INTERMEDIO",
        "descanso_segundos": 60,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Empuje",
                "ejercicios": [
                    ("Press inclinado con mancuernas", 4),
                    ("Fondos en máquina asistida o paralelas", 4),
                    ("Aperturas en polea", 3),
                    ("Press Arnold", 3),
                    ("Elevaciones laterales en polea", 3),
                    ("Extensión de tríceps en polea", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Tirón",
                "ejercicios": [
                    ("Dominadas", 4),
                    ("Remo en polea baja", 4),
                    ("Pull-over en polea alta", 3),
                    ("Elevaciones posteriores en máquina (Pájaros)", 3),
                    ("Curl con barra Z", 3),
                    ("Curl martillo con mancuernas", 3),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Pierna",
                "ejercicios": [
                    ("Sentadilla Hack en máquina", 4),
                    ("Peso muerto rumano", 4),
                    ("Zancadas caminando con mancuernas", 3),
                    ("Curl femoral sentado", 3),
                    ("Elevación de talones de pie", 4),
                    ("Elevación de piernas colgado", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Torso",
                "ejercicios": [
                    ("Press de banca con mancuernas", 4),
                    ("Jalón al pecho con agarre cerrado", 4),
                    ("Press militar con mancuernas sentado", 3),
                    ("Remo con mancuerna a una mano", 3),
                    ("Elevaciones laterales", 3),
                    ("Rueda abdominal", 3),
                ],
            },
            {
                "dia": "SAB",
                "nombre": "Pierna y glúteo",
                "ejercicios": [
                    ("Prensa de piernas", 4),
                    ("Hip thrust", 4),
                    ("Extensión de cuádriceps en máquina", 3),
                    ("Curl femoral tumbado", 3),
                    ("Elevación de talones sentado en máquina (Sóleo)", 3),
                    ("Crunch abdominal en polea o máquina", 3),
                ],
            },
        ],
    },
    {
        "nombre": "Torso / Pierna Definición Estética",
        "descripcion": "Cuatro días con prioridad en hombros, dorsal y abdomen para marcar la forma de V sin dejar de entrenar pesado.",
        "meta_objetivo": "DEFINIR",
        "somatotipo_ideal": "ECTOMORFO",
        "nivel": "INTERMEDIO",
        "descanso_segundos": 90,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Torso · hombros y dorsal",
                "ejercicios": [
                    ("Press militar con mancuernas sentado", 4),
                    ("Dominadas", 4),
                    ("Press inclinado con mancuernas", 3),
                    ("Elevaciones laterales", 4),
                    ("Remo con mancuerna a una mano", 3),
                    ("Face pull en polea", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Pierna y abdomen A",
                "ejercicios": [
                    ("Sentadilla libre", 4),
                    ("Peso muerto rumano", 3),
                    ("Extensión de cuádriceps en máquina", 3),
                    ("Curl femoral tumbado", 3),
                    ("Elevación de talones de pie", 4),
                    ("Elevación de piernas colgado", 3),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Torso · pecho y brazos",
                "ejercicios": [
                    ("Press de banca con mancuernas", 4),
                    ("Jalón al pecho en polea", 4),
                    ("Cruce de poleas de arriba abajo", 3),
                    ("Elevaciones laterales en polea", 3),
                    ("Curl martillo con mancuernas", 3),
                    ("Extensión de tríceps sobre la cabeza en polea", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Pierna y abdomen B",
                "ejercicios": [
                    ("Prensa de piernas", 4),
                    ("Zancadas / Búlgaras con mancuernas", 3),
                    ("Curl femoral sentado", 3),
                    ("Hip thrust", 3),
                    ("Elevación de talones sentado en máquina (Sóleo)", 4),
                    ("Crunch abdominal en polea o máquina", 3),
                ],
            },
        ],
    },
    {
        "nombre": "Glúteo & Pierna Prioridad + Torso (Strong Curves)",
        "descripcion": "Cuatro días con el glúteo como protagonista (hip thrust, peso muerto y zancadas), una sesión de pierna completa y otra de torso.",
        "meta_objetivo": "DEFINIR",
        "somatotipo_ideal": "TODOS",
        "nivel": "INTERMEDIO",
        "descanso_segundos": 90,
        "dias": [
            {
                "dia": "LUN",
                "nombre": "Glúteo · fuerza",
                "ejercicios": [
                    ("Hip thrust", 4),
                    ("Peso muerto rumano", 4),
                    ("Zancadas / Búlgaras con mancuernas", 3),
                    ("Aducción/Abducción de cadera en máquina", 3),
                    ("Patada de glúteo en polea", 3),
                ],
            },
            {
                "dia": "MAR",
                "nombre": "Torso",
                "ejercicios": [
                    ("Jalón al pecho en polea", 3),
                    ("Press inclinado con mancuernas", 3),
                    ("Remo en polea baja", 3),
                    ("Elevaciones laterales", 3),
                    ("Extensión de tríceps en polea", 3),
                    ("Plancha abdominal", 3),
                ],
            },
            {
                "dia": "JUE",
                "nombre": "Pierna completa",
                "ejercicios": [
                    ("Sentadilla libre", 4),
                    ("Prensa de piernas", 3),
                    ("Curl femoral sentado", 3),
                    ("Puente de glúteos", 3),
                    ("Subida al cajón (step-up)", 3),
                    ("Elevación de talones de pie", 3),
                ],
            },
            {
                "dia": "VIE",
                "nombre": "Glúteo · volumen",
                "ejercicios": [
                    ("Hip thrust en máquina", 4),
                    ("Peso muerto sumo", 3),
                    ("Sentadilla sumo con mancuerna", 3),
                    ("Pull-through en polea", 3),
                    ("Patada de glúteo en máquina", 3),
                    ("Elevación de piernas tumbado", 3),
                ],
            },
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

    if "rutina_ejercicios" in tablas:
        columnas_items = {c["name"] for c in inspector.get_columns("rutina_ejercicios")}
        if "dia_semana" not in columnas_items:
            # Plan por días: NULL = el ejercicio se hace todos los días de la rutina.
            db.session.execute(text("ALTER TABLE rutina_ejercicios ADD COLUMN dia_semana VARCHAR(3)"))
            db.session.commit()
    db.create_all()


def _definicion_plantilla(plantilla_def: dict, ejercicios_por_nombre: dict) -> dict:
    """Traduce la definición de una rutina famosa a lo que guarda el repositorio."""
    items: list[dict] = []
    nombres_dias: dict[str, str] = {}
    for dia in plantilla_def["dias"]:
        nombres_dias[dia["dia"]] = dia["nombre"]
        for nombre_ej, series_obj in dia["ejercicios"]:
            ejercicio = ejercicios_por_nombre[nombre_ej.strip().lower()]
            items.append(
                {
                    "ejercicio_id": ejercicio.id,
                    "orden": len(items) + 1,
                    "dia_semana": dia["dia"],
                    "descanso_segundos": plantilla_def["descanso_segundos"],
                    "series_objetivo": series_obj,
                }
            )
    return {
        "ejercicios_items": items,
        "nombres_dias": nombres_dias,
        "dias_semana": ",".join(dia["dia"] for dia in plantilla_def["dias"]),
        "descripcion": plantilla_def["descripcion"],
        "meta_objetivo": plantilla_def["meta_objetivo"],
        "somatotipo_ideal": plantilla_def["somatotipo_ideal"],
        "nivel": plantilla_def["nivel"],
    }


def _plantilla_al_dia(plantilla, definicion: dict) -> bool:
    """Indica si la plantilla guardada coincide con su definición (plan por días incluido)."""
    guardados = [
        (i.dia_semana, i.ejercicio_id, i.orden, i.series_objetivo, i.descanso_segundos)
        for i in sorted(plantilla.ejercicios, key=lambda x: x.orden)
    ]
    esperados = [
        (i["dia_semana"], i["ejercicio_id"], i["orden"], i["series_objetivo"], i["descanso_segundos"])
        for i in definicion["ejercicios_items"]
    ]
    return (
        guardados == esperados
        and {d.dia_semana: d.nombre for d in plantilla.dias} == definicion["nombres_dias"]
        and plantilla.dias_semana == definicion["dias_semana"]
        and plantilla.descripcion == definicion["descripcion"]
        and plantilla.meta_objetivo == definicion["meta_objetivo"]
        and plantilla.somatotipo_ideal == definicion["somatotipo_ideal"]
        and plantilla.nivel == definicion["nivel"]
    )


def seed_database(incluir_demo: bool = True) -> dict:
    """Crea tablas si no existen y puebla de forma idempotente grupos, ejercicios, 12 rutinas famosas y demo."""
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

    # Catálogo de las 12 Rutinas Famosas: se crean las que faltan y se reparan las que ya no
    # coinciden con su definición (p. ej. las antiguas, con la misma lista todos los días).
    plantillas_existentes = {
        r.nombre.strip().lower(): r for r in rutina_repo.listar_plantillas_famosas()
    }
    rutinas_famosas_creadas = 0
    rutinas_famosas_actualizadas = 0

    for plantilla_def in RUTINAS_FAMOSAS_BASE:
        clave_rutina = plantilla_def["nombre"].strip().lower()
        definicion = _definicion_plantilla(plantilla_def, ejercicios_existentes)
        existente = plantillas_existentes.get(clave_rutina)
        if existente is None:
            plantillas_existentes[clave_rutina] = rutina_repo.crear(
                usuario_id=None,
                nombre=plantilla_def["nombre"],
                es_favorita=False,
                es_plantilla_famosa=True,
                **definicion,
            )
            rutinas_famosas_creadas += 1
        elif not _plantilla_al_dia(existente, definicion):
            rutina_repo.actualizar(rutina=existente, **definicion)
            rutinas_famosas_actualizadas += 1

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
        "rutinas_famosas_actualizadas": rutinas_famosas_actualizadas,
        "total_grupos": len(grupos_existentes),
        "total_ejercicios": len(ejercicios_existentes),
        "total_rutinas_famosas": len(plantillas_existentes),
        "demo_email": DEMO_USER_EMAIL if incluir_demo else None,
        "demo_creado": demo_creado,
    }
