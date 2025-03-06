# app/routers/prompts.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
from app.dependencies import get_current_user
from app.supabase_client import supabase_admin

router = APIRouter(prefix="/prompts", tags=["Prompts"])

# --------------------------
# Request Models
# --------------------------
class CreatePromptRequest(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str]
    visibility: str  # e.g. "public" or "private"

class UpdatePromptRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None

class SharePromptRequest(BaseModel):
    prompt_id: str
    shared_with: str  # user id of the recipient
    permission_level: str = "read"
    expires_at: Optional[datetime.datetime] = None

# --------------------------
# Endpoints
# --------------------------

@router.get("/", response_model=List[dict])
def fetch_prompts(user: dict = Depends(get_current_user)):
    resp = supabase_admin.from_("prompts").select("*").execute()
    if hasattr(resp, "error") and resp.error:
        raise HTTPException(status_code=400, detail=resp.error.message)
    return resp.data

@router.post("/", response_model=dict)
def create_prompt(request: CreatePromptRequest, user: dict = Depends(get_current_user)):
    prompt_data = request.dict()
    prompt_data["user_id"] = user["id"]
    prompt_data["favorites_count"] = 0
    prompt_data["shared_count"] = 0
    prompt_data["access_count"] = 0
    now_iso = datetime.datetime.utcnow().isoformat()
    prompt_data["created_at"] = now_iso
    prompt_data["updated_at"] = now_iso

    insert_resp = supabase_admin.from_("prompts").insert(
        [prompt_data], returning="representation"
    ).execute()

    if hasattr(insert_resp, "error") and insert_resp.error:
        raise HTTPException(status_code=400, detail=insert_resp.error.message)
    if isinstance(insert_resp.data, list) and len(insert_resp.data) > 0:
        return insert_resp.data[0]
    return insert_resp.data

@router.patch("/{prompt_id}", response_model=dict)
def update_prompt(prompt_id: str, request: UpdatePromptRequest, user: dict = Depends(get_current_user)):
    update_data = request.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.datetime.utcnow().isoformat()
    update_resp = supabase_admin.from_("prompts").update(update_data) \
        .eq("id", prompt_id) \
        .eq("user_id", user["id"]) \
        .execute()
    if hasattr(update_resp, "error") and update_resp.error:
        raise HTTPException(status_code=400, detail=update_resp.error.message)
    if isinstance(update_resp.data, list) and len(update_resp.data) > 0:
        return update_resp.data[0]
    return update_resp.data

@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: str, user: dict = Depends(get_current_user)):
    delete_resp = supabase_admin.from_("prompts").delete() \
        .eq("id", prompt_id) \
        .eq("user_id", user["id"]) \
        .execute()
    if hasattr(delete_resp, "error") and delete_resp.error:
        raise HTTPException(status_code=400, detail=delete_resp.error.message)
    return {"detail": "Prompt deleted successfully"}

@router.post("/{prompt_id}/share", response_model=dict)
def share_prompt(prompt_id: str, request: SharePromptRequest, user: dict = Depends(get_current_user)):
    share_data = request.dict()
    share_data["shared_by"] = user["id"]
    if share_data.get("expires_at"):
        share_data["expires_at"] = share_data["expires_at"].isoformat()
    insert_resp = supabase_admin.from_("prompt_shares").insert(
        [share_data], returning="representation"
    ).execute()
    if hasattr(insert_resp, "error") and insert_resp.error:
        raise HTTPException(status_code=400, detail=insert_resp.error.message)
    if isinstance(insert_resp.data, list) and insert_resp.data:
        return insert_resp.data[0]
    return insert_resp.data

@router.delete("/{prompt_id}/share/{shared_with}")
def revoke_prompt_access(prompt_id: str, shared_with: str, user: dict = Depends(get_current_user)):
    delete_resp = supabase_admin.from_("prompt_shares").delete() \
        .match({"prompt_id": prompt_id, "shared_with": shared_with}) \
        .execute()
    if hasattr(delete_resp, "error") and delete_resp.error:
        raise HTTPException(status_code=400, detail=delete_resp.error.message)
    return {"detail": "Access revoked successfully"}

@router.get("/{prompt_id}/shares", response_model=List[dict])
def get_prompt_shares(prompt_id: str, user: dict = Depends(get_current_user)):
    resp = supabase_admin.from_("prompt_shares").select("*, shared_with:users(email)") \
        .eq("prompt_id", prompt_id) \
        .execute()
    if hasattr(resp, "error") and resp.error:
        raise HTTPException(status_code=400, detail=resp.error.message)
    return resp.data

@router.patch("/{prompt_id}/visibility", response_model=dict)
def update_visibility(prompt_id: str, visibility: str, user: dict = Depends(get_current_user)):
    update_resp = supabase_admin.from_("prompts").update({"visibility": visibility}) \
        .eq("id", prompt_id) \
        .eq("user_id", user["id"]) \
        .execute()
    if hasattr(update_resp, "error") and update_resp.error:
        raise HTTPException(status_code=400, detail=update_resp.error.message)
    return {"detail": "Visibility updated successfully"}
