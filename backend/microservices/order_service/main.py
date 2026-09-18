from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header
)

from jose import (
    jwt,
    JWTError,
    ExpiredSignatureError
)

from datetime import datetime

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from pydantic import BaseModel

from microservices.common.database import client

from microservices.common.config import (
    SECRET_KEY,
    ALGORITHM,
    ORDER_DB_NAME
)

import httpx
import uuid


security = HTTPBearer()

app = FastAPI()

# =========================
# DATABASE
# =========================

db = client[ORDER_DB_NAME]

order_collection = db["orders"]


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

class CheckoutRequest(BaseModel):
    full_name: str
    phone: str
    address: str
    city: str
    pincode: str


# =========================
# CHECKOUT
# =========================

@app.post("/checkout")
async def checkout(
    request: CheckoutRequest,
    user=Depends(get_current_user),
    authorization: str = Header(...)
):

    user_id = user["user_id"]

    async with httpx.AsyncClient() as client_http:

        response = await client_http.get(
            "http://127.0.0.1:8003/cart",
            headers={
                "Authorization": authorization
            }
        )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Cart fetch failed"
            )

        cart = response.json()

    if not cart or not cart["items"]:

        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    subtotal = sum(
        item["price"] * item["qty"]
        for item in cart["items"]
    )

    shipping_tax = 100

    tax_rate = 0.18

    tax_amount = subtotal * tax_rate

    total = subtotal + tax_amount + shipping_tax

    new_order_id = str(uuid.uuid4())

    await order_collection.insert_one({

        "order_id": new_order_id,

        "user_id": user_id,

        "email": user["email"],

        "items": cart["items"],

        "total": total,

        "shipping_cost": shipping_tax,

        "tax_cost": tax_amount,

        "status": "pending",

        "created_at": datetime.now(),

        "shipping_details": request.model_dump()

    })

    async with httpx.AsyncClient() as client_http:

        await client_http.delete(
            "http://127.0.0.1:8003/cart",
            headers={
                "Authorization": authorization
            }
        )

    return {
        "message": "Order placed successfully",
        "order_id": new_order_id
    }


# =========================
# GET ORDERS
# =========================

@app.get("/orders")
async def get_orders(user=Depends(get_current_user)):

    user_id = user["user_id"]

    cursor = order_collection.find(
        {"user_id": user_id},
        {"_id": 0}
    )

    orders = await cursor.to_list(length=None)

    return orders


@app.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    user=Depends(get_current_user)
):

    user_id = user["user_id"]

    order = await order_collection.find_one(
        {
            "order_id": order_id,
            "user_id": user_id
        },
        {
            "_id": 0
        }
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


# =========================
# CANCEL ORDER
# =========================

@app.put("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    user=Depends(get_current_user),
    authorization: str = Header(...)
):

    user_id = user["user_id"]

    order = await order_collection.find_one({
        "order_id": order_id,
        "user_id": user_id
    })

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order["user_id"] != user_id:

        raise HTTPException(
            status_code=403,
            detail="User does not have permission"
        )

    if order["status"] != "pending":

        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be canceled"
        )

    async with httpx.AsyncClient() as client_http:

        response = await client_http.post(
            "http://127.0.0.1:8003/restock_canceled_product",
            json={
                "items": order["items"]
            },
            headers={
                "Authorization": authorization
            }
        )

        if response.status_code != 200:

            raise HTTPException(
                status_code=400,
                detail="Order cancel failed"
            )

    await order_collection.update_one(
        {
            "order_id": order["order_id"]
        },
        {
            "$set": {
                "status": "cancelled"
            }
        }
    )

    return {
        "message": "Order canceled"
    }


# uvicorn microservices.order_service.main:app --reload --port 8004