@echo off

start cmd /k "call .venv\Scripts\activate && uvicorn microservices.auth_service.main:app --reload --port 8001"

start cmd /k "call .venv\Scripts\activate && uvicorn microservices.product_service.main:app --reload --port 8002"

start cmd /k "call .venv\Scripts\activate && uvicorn microservices.cart_service.main:app --reload --port 8003"

start cmd /k "call .venv\Scripts\activate && uvicorn microservices.order_service.main:app --reload --port 8004"

start cmd /k "call .venv\Scripts\activate && uvicorn microservices.admin_service.main:app --reload --port 8005"

start cmd /k "call .venv\Scripts\activate && uvicorn microservices.gateway.main:app --reload --port 8000"