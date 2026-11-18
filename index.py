"""Punto de entrada de FitTracker en Vercel (Vercel Functions detecta la variable ``app``).

Aquí no se crean tablas ni se ejecuta el seed: en serverless eso ocurriría en cada arranque en
frío. La base se prepara una vez, al desplegar, con ``flask --app index seed --no-demo``.
"""

import os

from app import create_app

app = create_app(os.environ.get("FLASK_CONFIG", "production"))
