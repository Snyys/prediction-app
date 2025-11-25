# prediction_app/api_gateway/Dockerfile
FROM docker.io/python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем таблицы и запускаем приложение
CMD sh -c "python init_db.py && uvicorn main:app --host 0.0.0.0 --port 80"