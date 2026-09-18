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

    product = await product_collection.find_one(
        {"product_id": int(product_id)}
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    cart = await cart_collection.find_one(
        {"user_id": user_id}
    )

    if not cart:
        cart = {
            "user_id": user_id,
            "items": []
        }

    items = cart.get("items", [])

    found = False

    for item in items:

        if item["product_id"] == int(product_id):

            if item["qty"] + 1 > product["qty"]:

                raise HTTPException(
                    status_code=400,
                    detail="Out of stock"
                )

            item["qty"] += 1

            found = True

            break

    if not found:

        items.append({
            "product_id": product["product_id"],
            "name": product["name"],
            "price": product["price"],
            "qty": 1,
            "image": product["image"]
        })

    await cart_collection.update_one(
        {"user_id": user_id},
        {"$set": {"items": items}},
        upsert=True
    )

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

    cart = await cart_collection.find_one({
        "user_id": user["user_id"]
    })

    if not cart:

        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    product = await product_collection.find_one({
        "product_id": product_id
    })

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    item_found = False

    for item in cart["items"]:

        if item["product_id"] == product_id:

            item_found = True

            if item["qty"] + 1 > product["qty"]:

                raise HTTPException(
                    status_code=400,
                    detail="Out of stock"
                )

            break

    if not item_found:

        raise HTTPException(
            status_code=404,
            detail="Item not found in cart"
        )

    await cart_collection.update_one(
        {
            "user_id": user["user_id"],
            "items.product_id": product_id
        },
        {
            "$inc": {
                "items.$.qty": 1
            }
        }
    )

    return {"message": "Item quantity increased"}


@app.put("/cart/decrease")
async def decrease_cart(
    product_id: int = Query(...),
    user=Depends(get_current_user)
):

    cart = await cart_collection.find_one({
        "user_id": user["user_id"]
    })

    if not cart:

        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    item_found = False

    for item in cart["items"]:

        if item["product_id"] == product_id:

            item_found = True

            if item["qty"] > 1:

                await cart_collection.update_one(
                    {
                        "user_id": user["user_id"],
                        "items.product_id": product_id
                    },
                    {
                        "$inc": {
                            "items.$.qty": -1
                        }
                    }
                )

            else:

                await cart_collection.update_one(
                    {
                        "user_id": user["user_id"]
                    },
                    {
                        "$pull": {
                            "items": {
                                "product_id": product_id
                            }
                        }
                    }
                )

            break

    if not item_found:

        raise HTTPException(
            status_code=404,
            detail="Item not found in cart"
        )

    return {"message": "Item quantity updated"}


# uvicorn microservices.cart_service.main:app --reload --port 8003