from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Query
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
    WISHLIST_DB_NAME,
    PRODUCT_DB_NAME
)


security = HTTPBearer()

app = FastAPI()

# =========================
# DATABASES
# =========================

wishlist_db = client[WISHLIST_DB_NAME]

product_db = client[PRODUCT_DB_NAME]

wishlist_collection = wishlist_db["wishlist"]

product_collection = product_db["products"]


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
# WISHLIST
# =========================

@app.get("/wishlist")
async def view_wishlist(
    user=Depends(get_current_user)
):

    wishlist = await wishlist_collection.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )

    return wishlist or {"items": []}


@app.post("/wishlist")
async def add_to_wishlist(
    product_id: int = Query(...),
    user=Depends(get_current_user)
):

    user_id = user["user_id"]

    product = await product_collection.find_one({
        "product_id": int(product_id)
    })

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    wishlist = await wishlist_collection.find_one({
        "user_id": user_id
    })

    if not wishlist:

        wishlist = {
            "user_id": user_id,
            "items": []
        }

    items = wishlist.get("items", [])

    for item in items:

        if item["product_id"] == int(product_id):

            return {
                "message": "Already in wishlist"
            }

    items.append({

        "product_id": product["product_id"],

        "name": product["name"],

        "price": product["price"],

        "image": product["image"]
    })

    await wishlist_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": items
            }
        },
        upsert=True
    )

    return {
        "message": "Wishlist updated",
        "items": items
    }


@app.delete("/wishlist/{product_id}")
async def remove_from_wishlist(
    product_id: int,
    user=Depends(get_current_user)
):

    await wishlist_collection.update_one(
        {"user_id": user["user_id"]},
        {
            "$pull": {
                "items": {
                    "product_id": product_id
                }
            }
        }
    )

    return {
        "message": "Item removed"
    }


# uvicorn microservices.wishlist_service.main:app --reload --port 8007