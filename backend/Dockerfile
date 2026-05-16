# Використовуємо офіційний легкий образ Python
FROM python:3.11-slim

# Налаштування змінних середовища
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Робоча директорія
WORKDIR /app

# Встановлення системних залежностей для MySQL та Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Встановлення Python залежностей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код додатка
COPY . .

# Збираємо статичні файли (WhiteNoise буде їх роздавати)
RUN python manage.py collectstatic --noinput

# Команда для запуску через Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "language_learning.wsgi:application"]
