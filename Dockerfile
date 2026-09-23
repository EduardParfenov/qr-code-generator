# Production-образ приложения qr-code-generator.
# Сборка:  docker build -t qr-code-generator .
# Запуск:  через docker compose (см. docker-compose.yml и readme, раздел «Запуск в Docker»)
FROM python:3.11-slim

# Логи сразу в stdout (их читает docker logs), не создавать .pyc в образе
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Сначала зависимости — слой кэшируется, пока requirements.txt не менялся
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения (только нужное для запуска)
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Порт gunicorn внутри контейнера (наружу пробрасывается в docker-compose.yml)
EXPOSE 8000

# Запуск через production WSGI-сервер; число workers — из GUNICORN_WORKERS (по умолчанию 2)
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:8000 -w ${GUNICORN_WORKERS:-2} app:app"]
