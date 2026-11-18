"""Punto de entrada para ejecutar el servidor de FitTracker."""

import os
from app import create_app, db
from app.seeds import seed_database

config_name = os.environ.get("FLASK_CONFIG", "default")
app = create_app(config_name)

with app.app_context():
    db.create_all()
    # El usuario demo tiene contraseña pública: nunca en producción.
    seed_database(incluir_demo=config_name != "production")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
