FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY microservices/review_service ./microservices/review_service
COPY microservices/common ./microservices/common

EXPOSE 8006

CMD ["uvicorn", "microservices.review_service.main:app", "--host", "0.0.0.0", "--port", "8006"]