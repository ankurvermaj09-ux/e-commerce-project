from fastapi import FastAPI, Query, HTTPException
import math
from pydantic import BaseModel

from microservices.common.database import client
from microservices.common.config import PRODUCT_DB_NAME, ORDER_DB_NAME

app = FastAPI()

# =========================
# DATABASE
# =========================

db = client[PRODUCT_DB_NAME]
order_db = client[ORDER_DB_NAME]

product_collection = db["products"]
store_details_collection = db["storedetails"]
order_collection = order_db["orders"]


# =========================
# MODELS
# =========================

class RestockItem(BaseModel):
    product_id: int
    qty: int


class RestockRequest(BaseModel):
    items: list[RestockItem]


# =========================
# HELPER
# =========================

async def paginated_products(
    filter_query: dict,
    page: int,
    limit: int,
    is_unfiltered: bool = False,
    sort_spec: list | None = None
) -> dict:
    if is_unfiltered:
        total = await product_collection.estimated_document_count()
    else:
        total = await product_collection.count_documents(filter_query, maxTimeMS=5000)

    skip = (page - 1) * limit
    projection = {"_id": 0}
    if sort_spec and any(isinstance(s, tuple) and len(s) > 1 and isinstance(s[1], dict) for s in sort_spec):
        projection["score"] = {"$meta": "textScore"}

    cursor = product_collection.find(filter_query, projection)
    if sort_spec:
        cursor = cursor.sort(sort_spec)
    cursor = cursor.skip(skip).limit(limit)

    products = await cursor.to_list(length=limit)
    for p in products:
        p.pop("score", None)

    return {
        "products": products,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if limit > 0 else 0
    }


# =========================
# PRODUCTS
# =========================

@app.get("/products")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    return await paginated_products({}, page, limit, is_unfiltered=True)


@app.get("/products/bestsellers")
@app.get("/bestsellers")
async def get_bestsellers():
    orders = await order_collection.find().to_list(length=None)

    sales = {}
    for order in orders:
        for item in order.get("items", []):
            pid = item.get("product_id")
            if not pid:
                continue
            if pid not in sales:
                sales[pid] = {
                    "product_id": pid,
                    "name": item.get("name", ""),
                    "image": item.get("image", ""),
                    "total_sold": 0
                }
            sales[pid]["total_sold"] += item.get("qty", 1)

    sorted_result = sorted(
        sales.values(),
        key=lambda x: x["total_sold"],
        reverse=True
    )[:5]

    return [
        {"product_id": p["product_id"], "name": p["name"], "image": p["image"]}
        for p in sorted_result
    ]


@app.get("/products/store_details")
@app.get("/store_details")
async def get_store_details():
    settings = await store_details_collection.find_one({"_id": "global_store_settings"})
    if settings:
        settings["_id"] = str(settings["_id"])
        return settings
    return {
        "store_name": "E-Commerce Store",
        "description": "Welcome to our store",
        "contact_email": "support@example.com"
    }


@app.get("/products/search")
async def search_products(
    q: str = Query(..., max_length=100),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    q_clean = q.strip()
    if not q_clean:
        return await paginated_products({}, page, limit, is_unfiltered=True)

    filter_query = {"$text": {"$search": q_clean}}
    return await paginated_products(
        filter_query,
        page,
        limit,
        sort_spec=[("score", {"$meta": "textScore"})]
    )


@app.get("/products/category/{cat_name}")
async def get_products_by_category(
    cat_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    filter_query = {"category": cat_name}
    return await paginated_products(filter_query, page, limit)


@app.get("/products/{product_id}")
async def get_product_by_id(product_id: int):
    product = await product_collection.find_one({"product_id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/restock_canceled_product")
async def restock_product(products: RestockRequest):
    for product in products.items:
        await product_collection.update_one(
            {
                "product_id": product.product_id
            },
            {
                "$inc": {
                    "qty": product.qty
                }
            }
        )

    return {
        "message": "Stock restored successfully"
    }