FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_CONFIG=production

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 5000

# --preload: run.py (crear tablas y seed) se ejecuta una sola vez, antes de crear los workers.
# Sin él, los dos workers hacían el seed a la vez sobre el mismo SQLite: el primer arranque
# fallaba o duplicaba el catálogo de ejercicios y rutinas.
CMD ["gunicorn", "--preload", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]

