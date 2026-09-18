from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import bcrypt

from jose import jwt, JWTError, ExpiredSignatureError

from datetime import datetime, timedelta

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from microservices.common.database import client

from microservices.common.config import (
    AUTH_DB_NAME,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI()

db = client[AUTH_DB_NAME]

users = db["users"]

user_collection = db["users"]

security = HTTPBearer()


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    full_name: str
    phone: str
    address: str
    city: str
    pincode: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )


@app.get("/")
def home():
    return {"services": "auth-service"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/count-users")
async def count_users():

    count = await users.count_documents({})

    return {"count": count}


# =========================
# JWT HELPERS
# =========================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


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
# AUTH
# =========================

@app.post("/register")
async def register(data: RegisterRequest):

    existing_user = await user_collection.find_one(
        {"email": data.email}
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    last_user = await user_collection.find_one(
        sort=[("user_id", -1)]
    )

    if last_user:
        new_user_id = last_user["user_id"] + 1
    else:
        new_user_id = 1

    user = {
        "user_id": new_user_id,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "role": "user"
    }

    await user_collection.insert_one(user)

    return {
        "message": "User registered successfully"
    }


@app.post("/login")
async def login(data: LoginRequest):

    user = await user_collection.find_one(
        {"email": data.email}
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        data.password,
        user["password_hash"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    print(
        f"--- LOGIN ATTEMPT --- Email received: {data.email}"
    )

    token = create_access_token({
        "user_id": user["user_id"],
        "email": user["email"],
        "role": user["role"]
    })

    return {"access_token": token}


# =========================
# USER PROFILE
# =========================

@app.put("/user/profile")
async def update_profile(
    profile: UserProfile,
    user=Depends(get_current_user)
):

    await user_collection.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "profile": profile.model_dump()
            }
        }
    )

    return {
        "message": "Profile updated successfully"
    }


@app.get("/user/profile")
async def get_profile(
    user=Depends(get_current_user)
):

    user_data = await user_collection.find_one(
        {"user_id": user["user_id"]},
        {
            "_id": 0,
            "password_hash": 0
        }
    )

    return user_data.get("profile") or {}