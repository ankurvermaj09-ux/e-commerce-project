FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY microservices/ticket_service ./microservices/ticket_service
COPY microservices/common ./microservices/common

EXPOSE 8008

CMD ["uvicorn", "microservices.ticket_service.main:app", "--host", "0.0.0.0", "--port", "8008"]