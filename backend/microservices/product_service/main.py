from fastapi import FastAPI
import math
from pydantic import BaseModel

from microservices.common.database import client

from microservices.common.config import PRODUCT_DB_NAME


app = FastAPI()

# =========================
# DATABASE
# =========================

db = client[PRODUCT_DB_NAME]

product_collection = db["products"]


# =========================
# MODELS
# =========================

class RestockItem(BaseModel):
    product_id: int
    qty: int


class RestockRequest(BaseModel):
    items: list[RestockItem]


# =========================
# PRODUCTS
# =========================

@app.get("/products")
async def get_products(page: int = 1, limit: int = 20):
    filter_query = {}
    total = await product_collection.count_documents(filter_query)
    cursor = product_collection.find(
        filter_query,
        {"_id": 0}
    ).skip((page - 1) * limit).limit(limit)

    products = await cursor.to_list(length=None)

    return {
        "products": products,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if limit > 0 else 0
    }


@app.get("/products/search")
async def search_products(q: str, page: int = 1, limit: int = 20):
    filter_query = {
        "name": {
            "$regex": q,
            "$options": "i"
        }
    }
    total = await product_collection.count_documents(filter_query)
    cursor = product_collection.find(
        filter_query,
        {
            "_id": 0
        }
    ).skip((page - 1) * limit).limit(limit)

    products = await cursor.to_list(length=None)

    return {
        "products": products,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if limit > 0 else 0
    }


@app.get("/products/category/{cat_name}")
async def get_products_by_category(cat_name: str, page: int = 1, limit: int = 20):
    filter_query = {
        "category": cat_name
    }
    total = await product_collection.count_documents(filter_query)
    cursor = product_collection.find(
        filter_query,
        {
            "_id": 0
        }
    ).skip((page - 1) * limit).limit(limit)

    products = await cursor.to_list(length=None)

    return {
        "products": products,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if limit > 0 else 0
    }


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


# uvicorn microservices.product_service.main:app --reload --port 8002