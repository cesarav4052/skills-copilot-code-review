"""
Endpoints for announcements in the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    expires_at: str
    starts_at: Optional[str] = None


def _parse_iso_datetime(raw_value: Optional[str], field_name: str) -> Optional[datetime]:
    if raw_value is None:
        return None

    try:
        normalized = raw_value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid ISO-8601 datetime"
        ) from exc


def _require_signed_in_user(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "message": document["message"],
        "starts_at": document.get("starts_at").isoformat() if document.get("starts_at") else None,
        "expires_at": document["expires_at"].isoformat(),
        "created_at": document.get("created_at").isoformat() if document.get("created_at") else None,
        "updated_at": document.get("updated_at").isoformat() if document.get("updated_at") else None,
    }


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get announcements currently active by start/end window."""
    now_utc = datetime.now(timezone.utc)
    query = {
        "expires_at": {"$gt": now_utc},
        "$or": [
            {"starts_at": {"$exists": False}},
            {"starts_at": None},
            {"starts_at": {"$lte": now_utc}}
        ]
    }

    cursor = announcements_collection.find(query).sort(
        [("starts_at", -1), ("expires_at", 1)]
    )

    return [_serialize_announcement(item) for item in cursor]


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all announcements for management. Requires authenticated user."""
    _require_signed_in_user(teacher_username)

    cursor = announcements_collection.find({}).sort([("expires_at", -1), ("created_at", -1)])
    return [_serialize_announcement(item) for item in cursor]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement. Requires authenticated user."""
    _require_signed_in_user(teacher_username)

    message = payload.message.strip()
    starts_at = _parse_iso_datetime(payload.starts_at, "starts_at")
    expires_at = _parse_iso_datetime(payload.expires_at, "expires_at")

    if expires_at is None:
        raise HTTPException(status_code=400, detail="expires_at is required")

    if starts_at and starts_at >= expires_at:
        raise HTTPException(status_code=400, detail="starts_at must be before expires_at")

    now_utc = datetime.now(timezone.utc)
    document = {
        "message": message,
        "starts_at": starts_at,
        "expires_at": expires_at,
        "created_at": now_utc,
        "updated_at": now_utc
    }

    result = announcements_collection.insert_one(document)
    created = announcements_collection.find_one({"_id": result.inserted_id})

    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an announcement. Requires authenticated user."""
    _require_signed_in_user(teacher_username)

    try:
        announcement_object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    message = payload.message.strip()
    starts_at = _parse_iso_datetime(payload.starts_at, "starts_at")
    expires_at = _parse_iso_datetime(payload.expires_at, "expires_at")

    if expires_at is None:
        raise HTTPException(status_code=400, detail="expires_at is required")

    if starts_at and starts_at >= expires_at:
        raise HTTPException(status_code=400, detail="starts_at must be before expires_at")

    update_result = announcements_collection.update_one(
        {"_id": announcement_object_id},
        {
            "$set": {
                "message": message,
                "starts_at": starts_at,
                "expires_at": expires_at,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": announcement_object_id})
    return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an announcement. Requires authenticated user."""
    _require_signed_in_user(teacher_username)

    try:
        announcement_object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.delete_one({"_id": announcement_object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
