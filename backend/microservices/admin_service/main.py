import shutil
from calendar import month_abbr
from datetime import datetime
import os
import re

from fastapi import FastAPI, Depends, Header, HTTPException, Query, status, Form, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from bson import ObjectId
from jose import jwt, JWTError, ExpiredSignatureError

from microservices.common.config import (
    SECRET_KEY,
    ALGORITHM,
    PRODUCT_DB_NAME,
    ORDER_DB_NAME,
    AUTH_DB_NAME
)
from microservices.common.database import client, next_sequence

security = HTTPBearer()
active_connections = []

app = FastAPI()

products_collection = client[PRODUCT_DB_NAME]["products"]
orders_collection = client[ORDER_DB_NAME]["orders"]
users_collection = client[AUTH_DB_NAME]["users"]
counters_collection = client[PRODUCT_DB_NAME]["counters"]


class StatusUpdate(BaseModel):
    status: str


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admin")
        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# ADMIN orders
# =========================
@app.get("/admin/orders")
async def admin_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    user=Depends(get_current_admin)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    match_stage = {}
    if status_filter:
        match_stage["status"] = status_filter

    skip = (page - 1) * limit
    pipeline = [
        {"$match": match_stage},
        {
            "$facet": {
                "metadata": [{"$count": "total"}],
                "orders": [
                    {"$sort": {"created_at": -1}},
                    {"$skip": skip},
                    {"$limit": limit}
                ]
            }
        }
    ]

    res = await orders_collection.aggregate(pipeline).to_list(length=1)
    facet = res[0] if res else {}

    total = facet.get("metadata", [{}])[0].get("total", 0) if facet.get("metadata") else 0
    orders = facet.get("orders", [])

    for o in orders:
        o["_id"] = str(o["_id"])

    return {
        "orders": orders,
        "total": total,
        "page": page,
        "limit": limit
    }


@app.put("/admin/orders/{order_id}/status")
async def update_status(order_id: str, status: str, user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    order = await orders_collection.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    transitions = {
        "pending": ["shipped", "cancelled"],
        "shipped": ["delivered"],
        "delivered": [],
        "cancelled": []
    }

    if status not in transitions[order["status"]]:
        raise HTTPException(status_code=400, detail="Invalid status change")

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}}
    )

    return {"message": "Status updated"}


# =========================
# ADMIN stats
# =========================

@app.get("/admin/stats")
async def admin_stats(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    now = datetime.now()
    start_of_this_month = datetime(now.year, now.month, 1)

    if now.month == 1:
        prev_year = now.year - 1
        prev_month = 12
    else:
        prev_year = now.year
        prev_month = now.month - 1

    start_of_last_month = datetime(prev_year, prev_month, 1)

    pipeline = [
        {
            "$facet": {
                "total_orders": [{"$count": "count"}],
                "cancelled_orders": [
                    {"$match": {"status": {"$regex": "^cancelled$", "$options": "i"}}},
                    {"$count": "count"}
                ],
                "delivered_stats": [
                    {"$match": {"status": {"$regex": "^delivered$", "$options": "i"}}},
                    {
                        "$group": {
                            "_id": None,
                            "total_revenue": {"$sum": "$total"},
                            "delivered_count": {"$sum": 1},
                            "this_month_revenue": {
                                "$sum": {
                                    "$cond": [
                                        {"$gte": ["$created_at", start_of_this_month]},
                                        "$total",
                                        0
                                    ]
                                }
                            },
                            "last_month_revenue": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$and": [
                                                {"$gte": ["$created_at", start_of_last_month]},
                                                {"$lt": ["$created_at", start_of_this_month]}
                                            ]
                                        },
                                        "$total",
                                        0
                                    ]
                                }
                            }
                        }
                    }
                ]
            }
        }
    ]

    res = await orders_collection.aggregate(pipeline).to_list(length=1)
    facet = res[0] if res else {}

    total_orders = facet.get("total_orders", [{}])[0].get("count", 0) if facet.get("total_orders") else 0
    cancelled_count = facet.get("cancelled_orders", [{}])[0].get("count", 0) if facet.get("cancelled_orders") else 0

    deliv_list = facet.get("delivered_stats", [])
    deliv = deliv_list[0] if deliv_list else {}

    total_revenue = deliv.get("total_revenue", 0)
    delivered_count = deliv.get("delivered_count", 0)
    this_month_revenue = deliv.get("this_month_revenue", 0)
    last_month_revenue = deliv.get("last_month_revenue", 0)

    cancellation_rate = (
        round((cancelled_count / total_orders) * 100, 2)
        if total_orders > 0 else 0
    )

    average_order_value = (
        round(total_revenue / delivered_count, 2)
        if delivered_count > 0 else 0
    )

    revenue_growth = (
        round(((this_month_revenue - last_month_revenue) / last_month_revenue) * 100, 2)
        if last_month_revenue > 0 else 0
    )

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "cancellation_rate": cancellation_rate,
        "average_order_value": average_order_value,
        "revenue_growth": revenue_growth
    }


@app.post("/admin/products")
async def add_product(
    name: str = Form(...),
    price: float = Form(...),
    qty: int = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    user=Depends(get_current_admin)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    product_id = await next_sequence(counters_collection, "product_id")

    await products_collection.insert_one({
        "product_id": product_id,
        "name": name,
        "price": price,
        "qty": qty,
        "category": category,
        "description": description,
        "image": file_path
    })

    return {"message": "Product added successfully"}


@app.get("/admin/stats/category_sales")
async def admin_category_sales(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    pipeline = [
        {"$match": {"status": {"$regex": "^delivered$", "$options": "i"}}},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.category",
                "revenue": {
                    "$sum": {
                        "$multiply": [
                            "$items.qty",
                            "$items.price"
                        ]
                    }
                }
            }
        },
        {"$sort": {"revenue": -1}}
    ]
    results = await orders_collection.aggregate(pipeline).to_list(length=None)

    formatted = [
        {
            "category": r["_id"] if r["_id"] is not None else "Uncategorized",
            "revenue": r["revenue"]
        }
        for r in results
    ]
    return formatted


@app.get("/admin/stats/monthly")
async def get_monthly_stats(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    try:
        pipeline = [
            {
                "$match": {
                    "status": "delivered"
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"}
                    },
                    "revenue": {"$sum": "$total"}
                }
            },
            {
                "$sort": {
                    "_id.year": 1,
                    "_id.month": 1
                }
            }
        ]

        results = await orders_collection.aggregate(pipeline).to_list(length=None)

        formatted = []
        for r in results:
            month_number = r["_id"]["month"]
            month_name = month_abbr[month_number]
            formatted.append({
                "month": month_name,
                "revenue": r["revenue"]
            })

        return formatted

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error calculating monthly stats")


@app.get("/admin/stats/bestsellers")
async def best_sellers(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    pipeline = [
        {"$match": {"status": "delivered"}},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "name": {"$first": "$items.name"},
                "image": {"$first": "$items.image"},
                "total_sold": {"$sum": "$items.qty"},
                "revenue": {"$sum": {"$multiply": ["$items.qty", "$items.price"]}}
            }
        },
        {"$sort": {"total_sold": -1}},
        {"$limit": 5},
        {
            "$project": {
                "_id": 0,
                "product_id": "$_id",
                "name": 1,
                "image": 1,
                "total_sold": 1,
                "revenue": 1
            }
        }
    ]

    products = await orders_collection.aggregate(pipeline).to_list(length=None)
    return {"products": products}


@app.get("/admin/stats/order-ratio")
async def order_status_ration(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        results = await orders_collection.aggregate(pipeline).to_list(length=None)
        data = {
            "delivered": 0,
            "cancelled": 0,
            "pending": 0,
            "shipped": 0,
        }
        for r in results:
            data[r["_id"]] = r["count"]

        return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error calculating order ratio")


@app.get("/admin/stats/pending")
async def pending_stats(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_admin)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    skip = (page - 1) * limit
    pipeline = [
        {"$match": {"status": "pending"}},
        {
            "$facet": {
                "metadata": [
                    {
                        "$group": {
                            "_id": None,
                            "pending_cost": {"$sum": "$total"},
                            "total": {"$sum": 1}
                        }
                    }
                ],
                "orders": [
                    {"$sort": {"created_at": -1}},
                    {"$skip": skip},
                    {"$limit": limit}
                ]
            }
        }
    ]

    res = await orders_collection.aggregate(pipeline).to_list(length=1)
    facet = res[0] if res else {}

    meta = facet.get("metadata", [{}])[0] if facet.get("metadata") else {}
    pending_cost = meta.get("pending_cost", 0)
    total = meta.get("total", 0)

    orders = facet.get("orders", [])
    for o in orders:
        o["_id"] = str(o["_id"])

    return {
        "pending_orders": orders,
        "pending_cost": pending_cost,
        "total": total,
        "page": page,
        "limit": limit
    }


@app.get("/admin/stats/cancelled")
async def cancelled_stats(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_admin)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    skip = (page - 1) * limit
    pipeline = [
        {"$match": {"status": "cancelled"}},
        {
            "$facet": {
                "metadata": [
                    {
                        "$group": {
                            "_id": None,
                            "cancelled_cost": {"$sum": "$total"},
                            "total": {"$sum": 1}
                        }
                    }
                ],
                "orders": [
                    {"$sort": {"created_at": -1}},
                    {"$skip": skip},
                    {"$limit": limit}
                ]
            }
        }
    ]

    res = await orders_collection.aggregate(pipeline).to_list(length=1)
    facet = res[0] if res else {}

    meta = facet.get("metadata", [{}])[0] if facet.get("metadata") else {}
    cancelled_cost = meta.get("cancelled_cost", 0)
    total = meta.get("total", 0)

    orders = facet.get("orders", [])
    for o in orders:
        o["_id"] = str(o["_id"])

    return {
        "cancelled_orders": orders,
        "cancelled_cost": cancelled_cost,
        "total": total,
        "page": page,
        "limit": limit
    }


@app.get("/admin/users/search")
async def search_users(
    q: str = Query(..., max_length=100),
    user=Depends(get_current_admin)
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    q_clean = q.strip()
    if not q_clean:
        return {"users": []}

    # Tradeoff: Anchored prefix regex (^re.escape(q)) allows MongoDB to utilize B-tree indexes on email/profile.full_name while preventing catastrophic backtracking, unlike unanchored regexes.
    safe_pattern = "^" + re.escape(q_clean)

    users = await users_collection.find(
        {
            "$or": [
                {"email": {"$regex": safe_pattern, "$options": "i"}},
                {"profile.full_name": {"$regex": safe_pattern, "$options": "i"}}
            ]
        },
        {"_id": 0, "password_hash": 0}
    ).to_list(length=None)

    return {"users": users}


@app.put("/admin/promote/{user_id}")
async def promote_to_admin(user_id: int, current_user=Depends(get_current_admin)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"role": "admin"}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User promoted successfully"}


@app.put("/admin/products/{product_id}/stock")
async def update_product_stock(product_id: int, qty: int, user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    result = await products_collection.update_one(
        {"product_id": product_id},
        {"$set": {"qty": qty}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Stock updated"}


@app.get("/admin/stats/top-customers")
async def get_top_customers(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    pipeline = [
        {"$match": {"status": "delivered"}},
        {"$group": {
            "_id": "$user_id",
            "email": {"$first": "$email"},
            "total_spent": {"$sum": "$total"},
            "order_count": {"$sum": 1}
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": 5}
    ]

    results = await orders_collection.aggregate(pipeline).to_list(length=None)
    return results
