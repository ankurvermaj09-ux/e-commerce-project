FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY microservices/cart_service ./microservices/cart_service
COPY microservices/common ./microservices/common

EXPOSE 8003

CMD ["uvicorn", "microservices.cart_service.main:app", "--host", "0.0.0.0", "--port", "8003"]