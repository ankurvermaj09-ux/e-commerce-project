from dotenv import load_dotenv
import os

load_dotenv()

# =========================
# MONGODB
# =========================

MONGO_URI = os.getenv("MONGO_URI")

AUTH_DB_NAME = os.getenv("AUTH_DB_NAME")

PRODUCT_DB_NAME = os.getenv("PRODUCT_DB_NAME")

CART_DB_NAME = os.getenv("CART_DB_NAME")

ORDER_DB_NAME = os.getenv("ORDER_DB_NAME")

REVIEW_DB_NAME = os.getenv("REVIEW_DB_NAME")

WISHLIST_DB_NAME = os.getenv("WISHLIST_DB_NAME")

TICKET_DB_NAME = os.getenv("TICKET_DB_NAME")


# =========================
# JWT
# =========================

SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
)


# =========================
# VALIDATION
# =========================

if not MONGO_URI:
    raise ValueError(
        "MONGO_URI is missing in .env"
    )

if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY is missing in .env"
    )

if not ALGORITHM:
    raise ValueError(
        "ALGORITHM is missing in .env"
    )

required_dbs = {

    "AUTH_DB_NAME": AUTH_DB_NAME,

    "PRODUCT_DB_NAME": PRODUCT_DB_NAME,

    "CART_DB_NAME": CART_DB_NAME,

    "ORDER_DB_NAME": ORDER_DB_NAME,

    "REVIEW_DB_NAME": REVIEW_DB_NAME,

    "WISHLIST_DB_NAME": WISHLIST_DB_NAME,

    "TICKET_DB_NAME": TICKET_DB_NAME
}

for key, value in required_dbs.items():

    if not value:

        raise ValueError(
            f"{key} is missing in .env"
        )