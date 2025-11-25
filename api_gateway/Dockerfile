FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . /app

# Создаем таблицы при запуске
CMD python init_db.py && uvicorn main:app --host 0.0.0.0 --port 80