FROM python:3.12-slim

# 1. Рабочая директория
WORKDIR /app

# 2. Копируем requirements.txt отдельно, чтобы кеш Docker не сбрасывался при каждом изменении кода
COPY requirements.txt .

# 3. Устанавливаем системные зависимости (при необходимости) и очищаем apt-кеш
RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

# 4. Устанавливаем python-зависимости
RUN pip install -r requirements.txt

# 5. Копируем всё остальное приложение
COPY . .

# 6. Полезные ENV
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1