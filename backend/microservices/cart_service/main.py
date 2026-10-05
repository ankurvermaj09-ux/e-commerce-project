from fastapi import FastAPI, Depends, HTTPException, Query

from jose import jwt, JWTError, ExpiredSignatureError

from datetime import datetime, timedelta

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from microservices.common.database import client

from microservices.common.config import (
    SECRET_KEY,
    ALGORITHM,
    CART_DB_NAME,
    PRODUCT_DB_NAME
)

security = HTTPBearer()

app = FastAPI()

# =========================
# DATABASES
# =========================

cart_db = client[CART_DB_NAME]

product_db = client[PRODUCT_DB_NAME]

cart_collection = cart_db["carts"]

product_collection = product_db["products"]


# =========================
# JWT AUTH
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
# CART (JWT BASED)
# =========================

@app.get("/cart")
async def view_cart(user=Depends(get_current_user)):

    cart = await cart_collection.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )

    return cart or {"items": []}


@app.post("/cart")
async def add_to_cart(
    product_id: int = Query(...),
    user=Depends(get_current_user)
):

    user_id = user["user_id"]
    pid = int(product_id)

    product = await product_collection.find_one(
        {"product_id": pid}
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product_qty = product.get("qty", 0)

    res = await cart_collection.update_one(
        {
            "user_id": user_id,
            "items": {
                "$elemMatch": {
                    "product_id": pid,
                    "qty": {"$lt": product_qty}
                }
            }
        },
        {"$inc": {"items.$.qty": 1}}
    )

    if res.matched_count == 0:

        existing_item = await cart_collection.find_one(
            {"user_id": user_id, "items.product_id": pid}
        )

        if existing_item:

            raise HTTPException(
                status_code=400,
                detail="Out of stock"
            )

        if product_qty < 1:

            raise HTTPException(
                status_code=400,
                detail="Out of stock"
            )

        new_item = {
            "product_id": product["product_id"],
            "name": product.get("name", ""),
            "price": product.get("price", 0),
            "qty": 1,
            "image": product.get("image", "")
        }

        await cart_collection.update_one(
            {"user_id": user_id},
            {"$push": {"items": new_item}},
            upsert=True
        )

    updated_cart = await cart_collection.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    items = updated_cart.get("items", []) if updated_cart else []

    return {
        "message": "Cart updated",
        "items": items
    }


@app.delete("/cart/{product_id}")
async def remove_from_cart(
    product_id: int,
    user=Depends(get_current_user)
):

    await cart_collection.update_one(
        {"user_id": user["user_id"]},
        {
            "$pull": {
                "items": {
                    "product_id": product_id
                }
            }
        }
    )

    return {"message": "Item removed"}


@app.delete("/cart")
async def clear_cart(user=Depends(get_current_user)):

    await cart_collection.delete_one(
        {"user_id": user["user_id"]}
    )

    return {"message": "Cart cleared"}


@app.put("/cart/increase")
async def increase_cart(
    product_id: int = Query(...),
    user=Depends(get_current_user)
):

    user_id = user["user_id"]
    pid = int(product_id)

    product = await product_collection.find_one({
        "product_id": pid
    })

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product_qty = product.get("qty", 0)

    res = await cart_collection.update_one(
        {
            "user_id": user_id,
            "items": {
                "$elemMatch": {
                    "product_id": pid,
                    "qty": {"$lt": product_qty}
                }
            }
        },
        {
            "$inc": {
                "items.$.qty": 1
            }
        }
    )

    if res.matched_count > 0:

        return {"message": "Item quantity increased"}

    cart = await cart_collection.find_one({
        "user_id": user_id
    })

    if not cart:

        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    item_in_cart = any(item.get("product_id") == pid for item in cart.get("items", []))

    if not item_in_cart:

        raise HTTPException(
            status_code=404,
            detail="Item not found in cart"
        )

    raise HTTPException(
        status_code=400,
        detail="Out of stock"
    )


@app.put("/cart/decrease")
async def decrease_cart(
    product_id: int = Query(...),
    user=Depends(get_current_user)
):

    user_id = user["user_id"]
    pid = int(product_id)

    res = await cart_collection.update_one(
        {
            "user_id": user_id,
            "items": {
                "$elemMatch": {
                    "product_id": pid,
                    "qty": {"$gt": 1}
                }
            }
        },
        {
            "$inc": {
                "items.$.qty": -1
            }
        }
    )

    if res.matched_count > 0:

        return {"message": "Item quantity updated"}

    res2 = await cart_collection.update_one(
        {
            "user_id": user_id,
            "items.product_id": pid
        },
        {
            "$pull": {
                "items": {
                    "product_id": pid
                }
            }
        }
    )

    if res2.matched_count > 0:

        return {"message": "Item quantity updated"}

    cart = await cart_collection.find_one({
        "user_id": user_id
    })

    if not cart:

        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    raise HTTPException(
        status_code=404,
        detail="Item not found in cart"
    )


# uvicorn microservices.cart_service.main:app --reload --port 8003