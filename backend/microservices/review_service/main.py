from fastapi import (
    FastAPI,
    HTTPException,
    Depends
)

from jose import (
    jwt,
    JWTError,
    ExpiredSignatureError
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from microservices.common.database import client

from microservices.common.config import (
    SECRET_KEY,
    ALGORITHM,
    REVIEW_DB_NAME,
    PRODUCT_DB_NAME,
    ORDER_DB_NAME,
    AUTH_DB_NAME
)

from datetime import datetime

from pydantic import (
    BaseModel,
    Field
)


security = HTTPBearer()

app = FastAPI()

# =========================
# DATABASES
# =========================

review_db = client[REVIEW_DB_NAME]
product_db = client[PRODUCT_DB_NAME]
order_db = client[ORDER_DB_NAME]
auth_db = client[AUTH_DB_NAME]

reviews_collection = review_db["reviews"]
products_collection = product_db["products"]
order_collection = order_db["orders"]
users_collection = auth_db["users"]


# =========================
# AUTH
# =========================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# =========================
# MODELS
# =========================

class Review(BaseModel):

    rating: int = Field(..., ge=1, le=5)

    comment: str


# =========================
# REVIEW
# =========================

@app.post("/products/{product_id}/reviews")
async def add_reviews(
    product_id: int,
    review_data: Review,
    user=Depends(get_current_user)
):

    verified_user_id = user["user_id"]

    product = await products_collection.find_one({
        "product_id": product_id
    })

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    order = await order_collection.find_one({
        "user_id": verified_user_id,
        "items.product_id": product_id
    })

    if not order:

        raise HTTPException(
            status_code=403,
            detail="You can only review products you purchased"
        )

    existing_review = await reviews_collection.find_one({
        "user_id": verified_user_id,
        "product_id": product_id
    })

    if existing_review:

        raise HTTPException(
            status_code=400,
            detail="You already reviewed this product"
        )

    # Resolve username at write time from auth_db users (fallback to email prefix)
    user_doc = await users_collection.find_one({"user_id": verified_user_id})
    username = user.get("email", "").split("@")[0] if user.get("email") else f"User {verified_user_id}"

    if user_doc:
        profile = user_doc.get("profile")
        if isinstance(profile, dict) and profile.get("full_name"):
            username = profile["full_name"]
        elif user_doc.get("name"):
            username = user_doc["name"]
        elif user_doc.get("email"):
            username = user_doc["email"].split("@")[0]

    new_review_data = {
        "user_id": verified_user_id,
        "product_id": product_id,
        "username": username,
        "rating": review_data.rating,
        "comment": review_data.comment,
        "created_at": datetime.now()
    }

    await reviews_collection.insert_one(
        new_review_data
    )

    return {
        "message": "Review added successfully"
    }


@app.get("/{product_id}")
@app.get("/reviews/{product_id}")
@app.get("/products/{product_id}/reviews")
async def get_reviews(product_id: int):

    cursor = reviews_collection.find(
        {"product_id": product_id},
        {
            "_id": 1,
            "product_id": 1,
            "user_id": 1,
            "username": 1,
            "rating": 1,
            "comment": 1,
            "created_at": 1
        }
    )

    reviews = await cursor.to_list(length=None)

    for r in reviews:
        r["_id"] = str(r["_id"])
        if "username" not in r or not r["username"]:
            r["username"] = f"User {r.get('user_id', '')}"

    return reviews