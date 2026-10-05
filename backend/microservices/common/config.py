from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env if present (will silently pass if .env does not exist in Docker)
load_dotenv(Path.cwd() / ".env")
load_dotenv()

# =========================
# MONGODB
# =========================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://172.16.22.174:27017/?directConnection=true")

AUTH_DB_NAME = os.getenv("AUTH_DB_NAME", "auth_db")
PRODUCT_DB_NAME = os.getenv("PRODUCT_DB_NAME", "product_db")
CART_DB_NAME = os.getenv("CART_DB_NAME", "cart_db")
ORDER_DB_NAME = os.getenv("ORDER_DB_NAME", "order_db")
REVIEW_DB_NAME = os.getenv("REVIEW_DB_NAME", "review_db")
WISHLIST_DB_NAME = os.getenv("WISHLIST_DB_NAME", "wishlist_db")
TICKET_DB_NAME = os.getenv("TICKET_DB_NAME", "ticket_db")

# =========================
# CORS
# =========================

CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(",") if origin.strip()]

# =========================
# MICROSERVICE URLS (FOR SERVICE-TO-SERVICE COMMUNICATION)
# =========================

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", os.getenv("AUTH_SERVICE", "http://127.0.0.1:8001"))
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", os.getenv("PRODUCT_SERVICE", "http://127.0.0.1:8002"))
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", os.getenv("CART_SERVICE", "http://127.0.0.1:8003"))
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", os.getenv("ORDER_SERVICE", "http://127.0.0.1:8004"))
ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL", os.getenv("ADMIN_SERVICE", "http://127.0.0.1:8005"))
REVIEW_SERVICE_URL = os.getenv("REVIEW_SERVICE_URL", os.getenv("REVIEW_SERVICE", "http://127.0.0.1:8006"))
WISHLIST_SERVICE_URL = os.getenv("WISHLIST_SERVICE_URL", os.getenv("WISHLIST_SERVICE", "http://127.0.0.1:8007"))
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", os.getenv("TICKET_SERVICE", "http://127.0.0.1:8008"))

# =========================
# JWT
# =========================

SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_key_here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
)

# =========================
# VALIDATION
# =========================

if not MONGO_URI:
    raise ValueError(
        "MONGO_URI environment variable is missing"
    )

if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable is missing"
    )

if not ALGORITHM:
    raise ValueError(
        "ALGORITHM environment variable is missing"
    )
