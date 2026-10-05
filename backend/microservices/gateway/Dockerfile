FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY microservices/gateway ./microservices/gateway
COPY microservices/common ./microservices/common

EXPOSE 8000

CMD ["uvicorn", "microservices.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]