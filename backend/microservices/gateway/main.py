from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

from microservices.common.config import (
    CORS_ORIGINS,
    AUTH_SERVICE_URL,
    PRODUCT_SERVICE_URL,
    CART_SERVICE_URL,
    ORDER_SERVICE_URL,
    ADMIN_SERVICE_URL,
    REVIEW_SERVICE_URL,
    WISHLIST_SERVICE_URL,
    TICKET_SERVICE_URL
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=2.0),
        limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
    )
    yield
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan)

# ==============================
# CORS
# ==============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# SERVICE URLS
# ==============================

AUTH_SERVICE = AUTH_SERVICE_URL
PRODUCT_SERVICE = PRODUCT_SERVICE_URL
CART_SERVICE = CART_SERVICE_URL
ORDER_SERVICE = ORDER_SERVICE_URL
ADMIN_SERVICE = ADMIN_SERVICE_URL
REVIEW_SERVICE = REVIEW_SERVICE_URL
WISHLIST_SERVICE = WISHLIST_SERVICE_URL
TICKET_SERVICE = TICKET_SERVICE_URL

# ==============================
# HELPER FUNCTION
# ==============================

HOP_BY_HOP = {
    "host", "content-length", "connection",
    "transfer-encoding", "keep-alive", "upgrade"
}

async def forward_request(
    request: Request,
    service_url: str,
    path: str
):
    url = f"{service_url}{path}"

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP
    }

    body = await request.body()
    client = request.app.state.http

    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={"content-type": response.headers.get("content-type", "application/json")}
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"detail": f"Gateway timeout communicating with downstream service at {service_url}"}
        )
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=502,
            content={"detail": f"Bad Gateway: Unable to reach downstream service at {service_url} ({exc})"}
        )

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