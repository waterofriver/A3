ARG BASE_REGISTRY=docker.io
FROM ${BASE_REGISTRY}/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml alembic.ini ./
COPY migrations ./migrations
COPY app ./app

RUN pip install --no-cache-dir . -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 300000 \
    && addgroup --system zhixue \
    && adduser --system --ingroup zhixue zhixue \
    && mkdir -p /app/data/courses /app/media \
    && chown -R zhixue:zhixue /app

USER zhixue
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
