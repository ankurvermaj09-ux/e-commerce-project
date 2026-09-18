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
    ORDER_DB_NAME
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

reviews_collection = review_db["reviews"]

products_collection = product_db["products"]

order_collection = order_db["orders"]


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

    new_review_data = {

        "user_id": verified_user_id,

        "product_id": product_id,

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


@app.get("/products/{product_id}/reviews")
async def get_reviews(product_id: int):

    pipeline = [

        {
            "$match": {
                "product_id": product_id
            }
        },

        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "user_info"
            }
        },

        {
            "$unwind": "$user_info"
        },

        {
            "$project": {
                "_id": 1,
                "rating": 1,
                "comment": 1,
                "created_at": 1,
                "username": "$user_info.name"
            }
        }
    ]

    cursor = reviews_collection.aggregate(
        pipeline
    )

    reviews = await cursor.to_list(length=None)

    for r in reviews:

        r["_id"] = str(r["_id"])

    return reviews


# uvicorn microservices.review_service.main:app --reload --port 8006