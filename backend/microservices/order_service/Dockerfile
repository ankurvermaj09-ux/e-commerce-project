FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY microservices/order_service ./microservices/order_service
COPY microservices/common ./microservices/common

EXPOSE 8004

CMD ["uvicorn", "microservices.order_service.main:app", "--host", "0.0.0.0", "--port", "8004"]