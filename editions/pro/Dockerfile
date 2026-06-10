FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libmariadb-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY editions/pro/requirements-pro.txt ./requirements-pro.txt
RUN pip install --no-cache-dir -r requirements-pro.txt

COPY app ./app
COPY rag_docs ./rag_docs
COPY fruits_data ./fruits_data

EXPOSE 8000 8601 8602
