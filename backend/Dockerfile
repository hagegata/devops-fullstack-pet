# ---- Stage 1: builder ----
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Stage 2: runtime ----
FROM python:3.12-slim

# Создаём непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Копируем установленные пакеты из builder
COPY --from=builder /root/.local /home/appuser/.local

COPY app.py .

# Даём права
RUN chown -R appuser:appuser /app

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "app.py"]
