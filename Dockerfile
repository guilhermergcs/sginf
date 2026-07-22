FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data \
    && useradd -m -r appuser \
    && chown -R appuser:appuser /app

RUN chmod +x entrypoint.sh

USER appuser

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
