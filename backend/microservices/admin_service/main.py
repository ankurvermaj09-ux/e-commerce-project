import shutil
from calendar import month_abbr

from fastapi import FastAPI,Depends,Header,HTTPException,Query,status,Form,UploadFile,File
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from pydantic import BaseModel
from bson import ObjectId
from pyexpat.errors import messages
from pymongo import MongoClient
from jose import jwt, JWTError,ExpiredSignatureError
from microservices.common.config import (
    SECRET_KEY,
    ALGORITHM,
    MONGO_URI,
    PRODUCT_DB_NAME,
    ORDER_DB_NAME,
    AUTH_DB_NAME
)
import httpx
import os


security=HTTPBearer()
active_connections=[]

app=FastAPI()


client = MongoClient(MONGO_URI)
products_collection = client[PRODUCT_DB_NAME]["products"]
orders_collection = client[ORDER_DB_NAME]["orders"]
users_collection = client[AUTH_DB_NAME]["users"]


class StatusUpdate(BaseModel):
    status: str




def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["role"]!="admin":
            raise HTTPException(status_code=403,detail="Only admin")
        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



# =========================
# ADMIN orders
# =========================
@app.get("/admin/orders")
def admin_orders(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    orders = list(orders_collection.find())
    for o in orders:
        o["_id"] = str(o["_id"])
    return orders


@app.put("/admin/orders/{order_id}/status")
def update_status(order_id: str, status: str, user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    order = orders_collection.find_one({"_id": ObjectId(order_id)})
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

    orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}}
    )

    return {"message": "Status updated"}



# =========================
# ADMIN stats
# =========================



@app.get("/admin/stats")
def admin_stats(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from datetime import datetime
    from calendar import monthrange

    now = datetime.now()
    start_of_this_month = datetime(now.year, now.month, 1)

    # Previous month
    if now.month == 1:
        prev_year = now.year - 1
        prev_month = 12
    else:
        prev_year = now.year
        prev_month = now.month - 1

    start_of_last_month = datetime(prev_year, prev_month, 1)

    # Fetch orders
    all_orders = list(orders_collection.find())
    delivered_orders = [o for o in all_orders if o["status"].lower() == "delivered"]
    cancelled_orders = [o for o in all_orders if o["status"].lower() == "cancelled"]

    total_orders = len(all_orders)
    total_revenue = sum(o.get("total", 0) for o in delivered_orders)

    # Cancellation Rate
    cancellation_rate = (
        (len(cancelled_orders) / total_orders) * 100
        if total_orders > 0 else 0
    )

    # Average Order Value
    average_order_value = (
        total_revenue / len(delivered_orders)
        if len(delivered_orders) > 0 else 0
    )

    # Revenue Growth %
    this_month_revenue = sum(
        o["total"] for o in delivered_orders
        if o["created_at"] >= start_of_this_month
    )

    last_month_revenue = sum(
        o["total"] for o in delivered_orders
        if start_of_last_month <= o["created_at"] < start_of_this_month
    )

    revenue_growth = (
        ((this_month_revenue - last_month_revenue) / last_month_revenue) * 100
        if last_month_revenue > 0 else 0
    )

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "cancellation_rate": round(cancellation_rate, 2),
        "average_order_value": round(average_order_value, 2),
        "revenue_growth": round(revenue_growth, 2)
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

    # 1️⃣ Create uploads folder if not exists
    os.makedirs("uploads", exist_ok=True)

    # 2️⃣ Save image
    file_path = f"uploads/{image.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # 3️⃣ Create product_id automatically
    product_id = products_collection.count_documents({}) + 1

    # 4️⃣ Insert into DB
    products_collection.insert_one({
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
def admin_stats(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        pipeline = [
            {"$match": {"status": {"$regex":"^delivered$", "$options":"i"}}},
            {"$unwind": "$items"},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "items.product_id",
                    "foreignField": "product_id",
                    "as": "product_info"
                }
            },
            {"$unwind": "$product_info"},
            {
                "$group": {
                    "_id": "$product_info.category",
                    "revenue": {
                        "$sum":{
                            "$multiply":[
                                "$items.qty",
                                "$items.price"
                            ]
                        }
                    }
                }
            },
            {"$sort": {"revenue": -1}},
        ]
        results=list(orders_collection.aggregate(pipeline))

        formatted=[
            {
                "category":r["_id"],
                "revenue":r["revenue"]
            }
            for r in results
        ]
        return formatted
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Product not found")



@app.get("/admin/stats/monthly")
def get_monthly_stats(user=Depends(get_current_admin)):
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

        results = list(orders_collection.aggregate(pipeline))

        formatted = []
        for r in results:
            month_number = r["_id"]["month"]
            month_name = month_abbr[month_number]  # Jan, Feb, Mar...
            formatted.append({
                "month": month_name,
                "revenue": r["revenue"]
            })

        return formatted

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error calculating monthly stats")




@app.get("/admin/stats/bestsellers")
def best_sellers(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    orders = list(orders_collection.find({"status":"delivered"}))

    sales = {}

    for order in orders:
        for item in order["items"]:
            pid = item["product_id"]

            if pid not in sales:
                sales[pid] = {
                    "product_id": pid,
                    "name": item["name"],
                    "image": item["image"],
                    "total_sold": 0,
                    "revenue": 0
                }

            sales[pid]["total_sold"] += item["qty"]
            sales[pid]["revenue"] += item["qty"] * item["price"]

    # Convert dict → list and sort
    result = sorted(
        sales.values(),
        key=lambda x: x["total_sold"],
        reverse=True
    )[:5]

    return {"products": result}


@app.get("/admin/stats/order-ratio")
def order_status_ration(user=Depends(get_current_admin)):
    if user["role"]!="admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        pipeline = [
            {
                "$group": {
                    "_id":"$status",
                    "count":{"$sum":1}
                }
            }
        ]
        results = list(orders_collection.aggregate(pipeline))
        data={
            "delivered":0,
            "cancelled":0,
            "pending":0,
            "shipped":0,
        }
        for r in results:
            data[r["_id"]]=r["count"]

        return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error calculating order ratio")



@app.get("/admin/stats/pending")
def pending_stats(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    orders = list(orders_collection.find({"status":"pending"}))
    total_pending_cost = sum(o.get("total", 0) for o in orders)
    for o in orders:
        o["_id"]=str(o["_id"])
    return {
        "pending_orders": orders,
        "pending_cost": total_pending_cost
    }


@app.get("/admin/stats/cancelled")
def cancelled_stats(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    orders = list(orders_collection.find({"status":"cancelled"}))
    cancelled_orders_cost= sum(o.get("total", 0) for o in orders)

    for o in orders:
        o["_id"] = str(o["_id"])
    return {
        "cancelled_orders": orders,
         "cancelled_cost": cancelled_orders_cost
    }




@app.get("/admin/users/search")
def search_users(q: str, user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # This searches both the email and the nested full_name inside profile
    users = list(
        users_collection.find(
            {
                "$or": [
                    {"email": {"$regex": q, "$options": "i"}},
                    {"profile.full_name": {"$regex": q, "$options": "i"}}
                ]
            },
            {"_id": 0, "password_hash": 0}
        )
    )

    return {"users": users}






@app.put("/admin/promote/{user_id}")
def promote_to_admin(user_id: int, current_user=Depends(get_current_admin)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Use the integer user_id instead of the MongoDB ObjectId
    result = users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"role": "admin"}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User promoted successfully"}


@app.put("/admin/products/{product_id}/stock")
def update_product_stock(product_id: int, qty: int, user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    result = products_collection.update_one(
        {"product_id": product_id},
        {"$set": {"qty": qty}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Stock updated"}


@app.get("/admin/stats/top-customers")
def get_top_customers(user=Depends(get_current_admin)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # Aggregate orders by user_id
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

    results = list(orders_collection.aggregate(pipeline))
    return results






#uvicorn microservices.admin_service.main:app --reload --port 8005
