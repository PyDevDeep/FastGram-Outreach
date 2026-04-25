FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Встановлення Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Кешування залежностей
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

# Копіювання коду
COPY . .

# Запуск через Uvicorn (порт 8000 всередині контейнера)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]