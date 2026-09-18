import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from microservices.common.database import client
from microservices.common.config import (
    SECRET_KEY,
    ALGORITHM,
    TICKET_DB_NAME
)

security = HTTPBearer()

app = FastAPI()

ticket_db = client[TICKET_DB_NAME]
ticket_collection = ticket_db["tickets"]

ALLOWED_PRIORITIES = ["low", "normal", "high"]
ALLOWED_STATUSES = ["open", "in_progress", "resolved", "closed"]


class CreateTicketRequest(BaseModel):
    order_id: str
    subject: str
    category: str
    priority: str
    description: str


class ReplyRequest(BaseModel):
    message: str


class StatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = None


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


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    payload = get_current_user(credentials)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return payload


@app.post("/tickets")
async def create_ticket(
    data: CreateTicketRequest,
    user=Depends(get_current_user)
):
    if not data.order_id or not data.order_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Order ID is required to raise a ticket"
        )

    if data.priority not in ALLOWED_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail="Invalid priority"
        )

    new_ticket_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    user_email = user.get("email", "")

    initial_history_entry = {
        "actor": "user",
        "actor_email": user_email,
        "action": "created",
        "message": data.description,
        "timestamp": now,
        "status": "open"
    }

    ticket_doc = {
        "ticket_id": new_ticket_id,
        "user_id": user["user_id"],
        "user_email": user_email,
        "subject": data.subject,
        "category": data.category,
        "order_id": data.order_id,
        "priority": data.priority,
        "status": "open",
        "created_at": now,
        "updated_at": now,
        "history": [initial_history_entry]
    }

    await ticket_collection.insert_one(ticket_doc)

    ticket_doc.pop("_id", None)
    return ticket_doc


@app.get("/tickets")
async def get_user_tickets(
    status: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    query = {"user_id": user["user_id"]}
    if status:
        query["status"] = status

    cursor = ticket_collection.find(
        query,
        {"_id": 0, "history": 0}
    ).sort("created_at", -1)

    tickets = await cursor.to_list(length=None)
    return tickets


@app.get("/tickets/{ticket_id}")
async def get_user_ticket_by_id(
    ticket_id: str,
    user=Depends(get_current_user)
):
    ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id, "user_id": user["user_id"]},
        {"_id": 0}
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket


@app.post("/tickets/{ticket_id}/messages")
async def user_reply_ticket(
    ticket_id: str,
    data: ReplyRequest,
    user=Depends(get_current_user)
):
    ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id, "user_id": user["user_id"]}
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    now = datetime.utcnow().isoformat()
    user_email = user.get("email", "")

    comment_entry = {
        "actor": "user",
        "actor_email": user_email,
        "action": "comment",
        "message": data.message,
        "timestamp": now
    }

    history_pushes = [comment_entry]
    new_status = ticket.get("status", "open")

    if ticket.get("status") in ["resolved", "closed"]:
        new_status = "open"
        status_change_entry = {
            "actor": "user",
            "actor_email": user_email,
            "action": "status_change",
            "message": "Reopened by user reply",
            "timestamp": now,
            "status": "open"
        }
        history_pushes.append(status_change_entry)

    await ticket_collection.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "status": new_status,
                "updated_at": now
            },
            "$push": {
                "history": {"$each": history_pushes}
            }
        }
    )

    updated_ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )
    return updated_ticket


@app.get("/admin/tickets/stats")
async def get_admin_ticket_stats(
    admin=Depends(get_current_admin)
):
    total = await ticket_collection.count_documents({})
    open_count = await ticket_collection.count_documents({"status": "open"})
    in_progress_count = await ticket_collection.count_documents({"status": "in_progress"})
    resolved_count = await ticket_collection.count_documents({"status": "resolved"})
    closed_count = await ticket_collection.count_documents({"status": "closed"})

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress_count,
        "resolved": resolved_count,
        "closed": closed_count
    }


@app.get("/admin/tickets")
async def get_admin_tickets(
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    query = {}
    if status:
        query["status"] = status

    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"subject": search_regex},
            {"user_email": search_regex}
        ]

    cursor = ticket_collection.find(
        query,
        {"_id": 0, "history": 0}
    ).sort("created_at", -1)

    tickets = await cursor.to_list(length=None)
    return tickets


@app.get("/admin/tickets/{ticket_id}")
async def get_admin_ticket_by_id(
    ticket_id: str,
    admin=Depends(get_current_admin)
):
    ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket


@app.post("/admin/tickets/{ticket_id}/messages")
async def admin_reply_ticket(
    ticket_id: str,
    data: ReplyRequest,
    admin=Depends(get_current_admin)
):
    ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id}
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    now = datetime.utcnow().isoformat()
    admin_email = admin.get("email", "")

    comment_entry = {
        "actor": "admin",
        "actor_email": admin_email,
        "action": "comment",
        "message": data.message,
        "timestamp": now
    }

    history_pushes = [comment_entry]
    new_status = ticket.get("status", "open")

    if ticket.get("status") == "open":
        new_status = "in_progress"
        status_change_entry = {
            "actor": "admin",
            "actor_email": admin_email,
            "action": "status_change",
            "message": "Moved to in_progress by admin reply",
            "timestamp": now,
            "status": "in_progress"
        }
        history_pushes.append(status_change_entry)

    await ticket_collection.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "status": new_status,
                "updated_at": now
            },
            "$push": {
                "history": {"$each": history_pushes}
            }
        }
    )

    updated_ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )
    return updated_ticket


@app.put("/admin/tickets/{ticket_id}/status")
async def update_admin_ticket_status(
    ticket_id: str,
    data: StatusUpdateRequest,
    admin=Depends(get_current_admin)
):
    if data.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id}
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    now = datetime.utcnow().isoformat()
    admin_email = admin.get("email", "")

    note_msg = data.note if data.note else f"Status changed to {data.status}"

    status_change_entry = {
        "actor": "admin",
        "actor_email": admin_email,
        "action": "status_change",
        "message": note_msg,
        "timestamp": now,
        "status": data.status
    }

    await ticket_collection.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "status": data.status,
                "updated_at": now
            },
            "$push": {
                "history": status_change_entry
            }
        }
    )

    updated_ticket = await ticket_collection.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )
    return updated_ticket
