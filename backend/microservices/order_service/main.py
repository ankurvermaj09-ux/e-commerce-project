from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header,
    Request
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
    ORDER_DB_NAME,
    PRODUCT_DB_NAME,
    CART_SERVICE_URL,
    PRODUCT_SERVICE_URL
)

import httpx
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=2.0),
        limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
    )
    yield
    await app.state.http.aclose()


security = HTTPBearer()

app = FastAPI(lifespan=lifespan)

# =========================
# DATABASE
# =========================

db = client[ORDER_DB_NAME]
order_collection = db["orders"]

product_db = client[PRODUCT_DB_NAME]
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
    request_data: CheckoutRequest,
    raw_request: Request,
    user=Depends(get_current_user),
    authorization: str = Header(...)
):

    user_id = user["user_id"]
    client_http = raw_request.app.state.http

    try:
        response = await client_http.get(
            f"{CART_SERVICE_URL}/cart",
            headers={
                "Authorization": authorization
            }
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cart service unreachable: {exc}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Cart fetch failed"
        )

    cart = response.json()

    if not cart or not cart.get("items"):
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    product_ids = list(set(item["product_id"] for item in cart["items"]))
    product_docs = await product_collection.find(
        {"product_id": {"$in": product_ids}},
        {"product_id": 1, "category": 1, "_id": 0}
    ).to_list(length=None)

    category_map = {p["product_id"]: p.get("category", "Uncategorized") for p in product_docs}

    enriched_items = []
    for item in cart["items"]:
        item_copy = dict(item)
        item_copy["category"] = category_map.get(item["product_id"], "Uncategorized")
        enriched_items.append(item_copy)

    subtotal = sum(
        item["price"] * item["qty"]
        for item in enriched_items
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
        "items": enriched_items,
        "total": total,
        "shipping_cost": shipping_tax,
        "tax_cost": tax_amount,
        "status": "pending",
        "created_at": datetime.now(),
        "shipping_details": request_data.model_dump()
    })

    try:
        await client_http.delete(
            f"{CART_SERVICE_URL}/cart",
            headers={
                "Authorization": authorization
            }
        )
    except httpx.RequestError:
        pass

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
    raw_request: Request,
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

    client_http = raw_request.app.state.http

    try:
        response = await client_http.post(
            f"{PRODUCT_SERVICE_URL}/restock_canceled_product",
            json={
                "items": order["items"]
            },
            headers={
                "Authorization": authorization
            }
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Restock service unreachable: {exc}"
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