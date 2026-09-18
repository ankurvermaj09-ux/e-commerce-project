from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from microservices.common.database import client

app = FastAPI()

db = client["test_db"]

# ==============================
# CORS
# ==============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# SERVICE URLS
# ==============================

AUTH_SERVICE = "http://127.0.0.1:8001"
PRODUCT_SERVICE = "http://127.0.0.1:8002"
CART_SERVICE = "http://127.0.0.1:8003"
ORDER_SERVICE = "http://127.0.0.1:8004"
ADMIN_SERVICE = "http://127.0.0.1:8005"
REVIEW_SERVICE = "http://127.0.0.1:8006"
WISHLIST_SERVICE = "http://127.0.0.1:8007"
TICKET_SERVICE = "http://127.0.0.1:8008"

# ==============================
# HELPER FUNCTION
# ==============================

async def forward_request(
    request: Request,
    service_url: str,
    path: str
):
    url = f"{service_url}{path}"

    headers = dict(request.headers)

    body = await request.body()

    async with httpx.AsyncClient() as client:

        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=body
        )

    try:
        return response.json()
    except Exception:
        return {
            "status_code": response.status_code,
            "content": response.text
        }

# ==============================
# AUTH SERVICE
# ==============================

@app.api_route(
    "/api/auth/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def auth_gateway(path: str, request: Request):

    return await forward_request(
        request,
        AUTH_SERVICE,
        f"/{path}"
    )

# ==============================
# PRODUCT SERVICE
# ==============================

@app.api_route(
    "/api/products/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def product_gateway(path: str, request: Request):

    return await forward_request(
        request,
        PRODUCT_SERVICE,
        f"/products/{path}"
    )

@app.get("/api/products")
async def get_products(request: Request):

    return await forward_request(
        request,
        PRODUCT_SERVICE,
        "/products"
    )

# ==============================
# CART SERVICE
# ==============================

@app.api_route(
    "/api/cart/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def cart_gateway(path: str, request: Request):

    return await forward_request(
        request,
        CART_SERVICE,
        f"/cart/{path}"
    )

@app.api_route(
    "/api/cart",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def cart_root(request: Request):

    return await forward_request(
        request,
        CART_SERVICE,
        "/cart"
    )

# ==============================
# ORDER SERVICE
# ==============================

@app.api_route(
    "/api/orders",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def orders_root(request: Request):

    return await forward_request(
        request,
        ORDER_SERVICE,
        "/orders"
    )


@app.api_route(
    "/api/orders/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def order_gateway(path: str, request: Request):

    return await forward_request(
        request,
        ORDER_SERVICE,
        f"/orders/{path}"
    )

@app.post("/api/checkout")
async def checkout_gateway(request: Request):

    return await forward_request(
        request,
        ORDER_SERVICE,
        "/checkout"
    )

# ==============================
# WISHLIST SERVICE
# ==============================

@app.api_route(
    "/api/wishlist/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def wishlist_gateway(path: str, request: Request):

    target_path = f"/wishlist/{path}" if path else "/wishlist"

    return await forward_request(
        request,
        WISHLIST_SERVICE,
        target_path
    )

@app.api_route(
    "/api/wishlist",
    methods=["GET", "POST", "DELETE"]
)
async def wishlist_root(request: Request):

    return await forward_request(
        request,
        WISHLIST_SERVICE,
        "/wishlist"
    )

# ==============================
# REVIEW SERVICE
# ==============================

@app.api_route(
    "/api/reviews/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def review_gateway(path: str, request: Request):

    return await forward_request(
        request,
        REVIEW_SERVICE,
        f"/{path}"
    )

# ==============================
# TICKET SERVICE
# ==============================

@app.api_route(
    "/api/tickets/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def ticket_gateway_path(path: str, request: Request):

    return await forward_request(
        request,
        TICKET_SERVICE,
        f"/tickets/{path}"
    )

@app.api_route(
    "/api/tickets",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def ticket_gateway_root(request: Request):

    return await forward_request(
        request,
        TICKET_SERVICE,
        "/tickets"
    )

# WARNING: Register /api/admin/tickets routes ABOVE the /api/admin/{path:path} catch-all, or FastAPI will swallow them and forward to ADMIN_SERVICE on 8005.

@app.api_route(
    "/api/admin/tickets/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def admin_ticket_gateway_path(path: str, request: Request):

    return await forward_request(
        request,
        TICKET_SERVICE,
        f"/admin/tickets/{path}"
    )

@app.api_route(
    "/api/admin/tickets",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def admin_ticket_gateway_root(request: Request):

    return await forward_request(
        request,
        TICKET_SERVICE,
        "/admin/tickets"
    )

# ==============================
# ADMIN SERVICE
# ==============================

@app.api_route(
    "/api/admin/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def admin_gateway(path: str, request: Request):

    return await forward_request(
        request,
        ADMIN_SERVICE,
        f"/admin/{path}"
    )

# ==============================
# HEALTH CHECK
# ==============================

@app.get("/")
def home():
    return {
        "message": "API Gateway Running"


    }

@app.get("/test-db")
async def test_db():
    result = await db.test.insert_one({"message": "Atlas Connected"})
    return {"inserted_id": str(result.inserted_id)}

#uvicorn microservices.gateway.main:app --reload --port 8000