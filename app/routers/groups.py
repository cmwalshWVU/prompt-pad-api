from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from app.dependencies import get_current_user  # This dependency returns the authenticated user as a dict
from app.supabase_client import supabase_admin

router = APIRouter(prefix="/groups", tags=["Groups"])

# --------------------------
# Models for Group operations
# --------------------------
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    privacy: Optional[str] = "private"  # could be "public" or "private"

class CreateGroupRequest(GroupBase):
    pass

class UpdateGroupRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    privacy: Optional[str] = None

class CreateGroupRequest(BaseModel):
    name: str
    description: str
    privacy: str

# --------------------------
# Endpoints for Groups
# --------------------------

@router.get("/", response_model=List[dict])
def fetch_groups(user: dict = Depends(get_current_user)):
    """
    Fetch all groups accessible to the current user. This includes:
      - Groups with public privacy.
      - Groups in which the user is a member.
    """
    # First, get all group memberships for the current user.
    print("User object:", user)

    member_resp = supabase_admin.from_("group_members").select("group_id").eq("user_id", user["sub"]).execute()
    if not member_resp.data:
        raise HTTPException(status_code=400, detail=member_resp.error.message)
    member_group_ids = [m["group_id"] for m in (member_resp.data or [])]

    # Build an OR filter: public groups OR groups the user is a member of.
    if member_group_ids:
        filter_clause = f"privacy.eq.public,id.in.({','.join(member_group_ids)})"
    else:
        filter_clause = "privacy.eq.public"

    groups_resp = supabase_admin.from_("groups") \
        .select("*, members:group_members(user_id)") \
        .or_(filter_clause) \
        .order("name") \
        .execute()

    if not groups_resp.data:
        raise HTTPException(status_code=400, detail=groups_resp.error.message)

    # Mark each group with a boolean indicating membership.
    processed_groups = []
    for group in groups_resp.data or []:
        group["is_member"] = any(m["user_id"] == user["sub"] for m in group.get("members", []))
        processed_groups.append(group)
    return processed_groups

@router.post("/", response_model=dict)
def create_group(request: CreateGroupRequest, user: dict = Depends(get_current_user)):
    """
    Create a new group. The request must include 'name', 'description', and 'privacy'.
    The current user's ID is stored as created_by.
    """
    group_data = request.dict()
    group_data["created_by"] = user["sub"]

    # Insert the new group and request that the inserted record be returned.
    insert_resp = supabase_admin.from_("groups") \
        .insert([group_data], returning="representation") \
        .execute()

    if not insert_resp.data:
        raise HTTPException(status_code=400, detail=insert_resp.error.message)

    # The response's data is expected to be a list with the inserted record.
    if isinstance(insert_resp.data, list) and len(insert_resp.data) > 0:
        return insert_resp.data[0]
    else:
        # Fallback: return the raw data.
        return insert_resp.data

@router.patch("/{group_id}", response_model=dict)
def update_group(
    group_id: str, 
    updates: UpdateGroupRequest, 
    user: dict = Depends(get_current_user)
):
    update_data = updates.dict(exclude_unset=True)
    # Use 'returning="representation"' to have the server return the updated record.
    update_resp = supabase_admin.from_("groups") \
        .update(update_data, returning="representation") \
        .eq("id", group_id) \
        .execute()

    if not update_resp.data:
        raise HTTPException(status_code=400, detail=update_resp.error.message)

    # Expecting the response data to be a list with one element (the updated record).
    if isinstance(update_resp.data, list) and update_resp.data:
        return update_resp.data[0]
    
    # Fallback in case the data is already a dictionary.
    return update_resp.data

@router.delete("/{group_id}")
def delete_group(group_id: str, user: dict = Depends(get_current_user)):
    """
    Delete a group.
    """
    delete_resp = supabase_admin.from_("groups") \
        .delete() \
        .eq("id", group_id) \
        .execute()
    if not delete_resp.data:
        raise HTTPException(status_code=400, detail=delete_resp.error.message)
    return {"detail": "Group deleted successfully"}

# --------------------------
# Endpoints for Group Members
# --------------------------

class AddMemberRequest(BaseModel):
    user_id: str
    role: Optional[str] = "member"

@router.get("/{group_id}/members", response_model=List[dict])
def fetch_members(group_id: str, user: dict = Depends(get_current_user)):
    resp = supabase_admin.from_("group_member_details") \
        .select("*") \
        .eq("group_id", group_id) \
        .order("joined_at") \
        .execute()
    print(resp)
    if hasattr(resp, "error"):
        raise HTTPException(status_code=400, detail=resp.error.message)
    return resp.data or []

@router.post("/{group_id}/members", response_model=dict)
def add_member(
    group_id: str,
    request: AddMemberRequest,
    user: dict = Depends(get_current_user)
):
    try:
        insert_resp = supabase_admin.from_("group_members").insert(
            [{
                "group_id": group_id,
                "user_id": request.user_id,
                "role": request.role
            }],
            returning="representation"
        ).execute()
    except Exception as e:
        # Log the error if needed, and check if it's a foreign key violation.
        raise HTTPException(
            status_code=400,
            detail="The specified group does not exist."
        )

    if hasattr(insert_resp, "error"):
        raise HTTPException(status_code=400, detail=insert_resp.error.message)
    
    if isinstance(insert_resp.data, list) and insert_resp.data:
        return insert_resp.data[0]
    return insert_resp.data

class UpdateMemberRoleRequest(BaseModel):
    role: str

@router.patch("/{group_id}/members/{member_id}", response_model=dict)
def update_member_role(group_id: str, member_id: str, request: UpdateMemberRoleRequest, user: dict = Depends(get_current_user)):
    update_resp = supabase_admin.from_("group_members") \
        .update({"role": request.role}) \
        .match({"group_id": group_id, "user_id": member_id}) \
        .select() \
        .single() \
        .execute()
    if hasattr(update_resp, "error"):
        raise HTTPException(status_code=400, detail=update_resp.error.message)
    return update_resp.data

@router.delete("/{group_id}/members/{member_id}")
def remove_member(group_id: str, member_id: str, user: dict = Depends(get_current_user)):
    delete_resp = supabase_admin.from_("group_members") \
        .delete() \
        .match({"group_id": group_id, "user_id": member_id}) \
        .execute()
    if hasattr(delete_resp, "error"):
        raise HTTPException(status_code=400, detail=delete_resp.error.message)
    return {"detail": "Member removed successfully"}

# --------------------------
# Endpoints for Group Prompts
# --------------------------

@router.get("/{group_id}/prompts", response_model=List[dict])
def fetch_group_prompts(group_id: str, user: dict = Depends(get_current_user)):
    resp = supabase_admin.from_("group_prompt_details") \
        .select("*") \
        .eq("group_id", group_id) \
        .order("shared_at") \
        .execute()
    if hasattr(resp, "error"):
        raise HTTPException(status_code=400, detail=resp.error.message)
    return resp.data or []

@router.post("/{group_id}/prompts/{prompt_id}")
def share_prompt(group_id: str, prompt_id: str, user: dict = Depends(get_current_user)):
    """
    Insert a record into the group_prompts table to share a prompt with a group.
    """
    data = {
        "group_id": group_id,
        "prompt_id": prompt_id,
        "shared_by": user["sub"],  # Optionally track who shared the prompt
        # Optionally add a "shared_at" field if not automatically handled by the database
    }
    
    # Insert the record and request the inserted record be returned.
    insert_resp = supabase_admin.from_("group_prompts").insert([data], returning="representation").execute()

    if hasattr(insert_resp, "error"):
        raise HTTPException(status_code=400, detail=insert_resp.error.message)

    # Check if data is returned as a list.
    if isinstance(insert_resp.data, list) and insert_resp.data:
        return {"detail": "Prompt shared successfully", "data": insert_resp.data[0]}
    
    # Fallback: return the raw data.
    return {"detail": "Prompt shared successfully", "data": insert_resp.data}

@router.delete("/{group_id}/prompts/{prompt_id}")
def unshare_prompt(group_id: str, prompt_id: str, user: dict = Depends(get_current_user)):
    resp = supabase_admin.from_("group_prompts") \
        .delete() \
        .match({"group_id": group_id, "prompt_id": prompt_id}) \
        .execute()
    if hasattr(resp, "error"):
        raise HTTPException(status_code=400, detail=resp.error.message)
    return {"detail": "Prompt unshared successfully"}

# --------------------------
# Endpoints for Group Invites
# --------------------------

@router.get("/invites", response_model=List[dict])
def fetch_invites(user: dict = Depends(get_current_user)):
    resp = supabase_admin.from_("group_invite_details") \
        .select("*") \
        .eq("email", user["email"]) \
        .eq("status", "pending") \
        .order("created_at") \
        .execute()
    if hasattr(resp, "data"):
        raise HTTPException(status_code=400, detail=resp.error.message)
    return resp.data or []

class InviteMemberRequest(BaseModel):
    email: str

@router.post("/{group_id}/invites", response_model=dict)
def invite_member(
    group_id: str,
    request: InviteMemberRequest,
    user: dict = Depends(get_current_user)
):
    insert_resp = supabase_admin.from_("group_invites").insert(
        [{
            "group_id": group_id,
            "email": request.email,
            "invited_by": user["sub"]
        }],
        returning="representation"  # Request the inserted record to be returned.
    ).execute()

    if hasattr(insert_resp, "error"):
        raise HTTPException(status_code=400, detail=insert_resp.error.message)

    # If data is returned as a list, return the first element.
    if isinstance(insert_resp.data, list) and len(insert_resp.data) > 0:
        return insert_resp.data[0]

    # Fallback: return the raw data.
    return insert_resp.data

@router.delete("/invites/{invite_id}")
def cancel_invite(invite_id: str, user: dict = Depends(get_current_user)):
    delete_resp = supabase_admin.from_("group_invites") \
        .delete() \
        .eq("id", invite_id) \
        .execute()
    if not delete_resp.data:
        raise HTTPException(status_code=400, detail=delete_resp.error.message)
    return {"detail": "Invite canceled successfully"}

@router.post("/invites/{invite_id}/accept")
def accept_invite(invite_id: str, user: dict = Depends(get_current_user)):
    resp = supabase_admin.rpc("accept_group_invite", {"invite_id": invite_id})
    if resp.error:
        raise HTTPException(status_code=400, detail=resp.error.message)
    # Optionally refresh groups after accepting the invite.
    return {"detail": "Invite accepted successfully"}

@router.post("/invites/{invite_id}/decline")
def decline_invite(invite_id: str, user: dict = Depends(get_current_user)):
    update_resp = supabase_admin.from_("group_invites") \
        .update({"status": "declined"}) \
        .eq("id", invite_id) \
        .execute()
    if not update_resp.data:
        raise HTTPException(status_code=400, detail=update_resp.error.message)
    return {"detail": "Invite declined successfully"}
