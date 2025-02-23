from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
import uuid
from app.supabase_client import supabase_admin
from app.dependencies import get_current_user
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- Request Models ---
class SignInRequest(BaseModel):
    email: str
    password: str

class SignUpRequest(BaseModel):
    email: str
    password: str

class UpdateProfileRequest(BaseModel):
    username: str | None = None
    avatar_url: str | None = None
    # Add additional fields as needed

# --- Public Endpoints ---

@router.post("/signin")
def sign_in(data: SignInRequest):
    # Call the Supabase admin client's sign-in method
    response = supabase_admin.auth.sign_in_with_password({
        "email": data.email,
        "password": data.password
    })
    
    # Check if the sign in was successful by verifying if 'user' is present.
    if not response.user:
        # You might also check 'session' if that's your preferred indicator.
        raise HTTPException(status_code=400, detail="Sign in failed: Invalid credentials or no user returned")
    
    # Return the response as a dictionary
    return response.dict()


@router.post("/signup")
def sign_up(data: SignUpRequest):
    """
    Sign up a new user.
    This endpoint is public and creates a new user.
    """
    response = supabase_admin.auth.sign_up({
        "email": data.email,
        "password": data.password
    })
    if response.get("error"):
        raise HTTPException(status_code=400, detail=response["error"].get("message", "Sign up failed"))
    return response

# --- Protected Endpoints (require a valid token) ---

@router.get("/user")
def get_user(user: dict = Depends(get_current_user)):
    """
    Retrieve the current user's information and profile.
    The `user` is injected by the `get_current_user` dependency.
    """
    logger.info(user)
    profile_resp = (
        supabase_admin
        .from_("user_profiles")
        .select("*")
        .eq("id", user["sub"])
        .single()
        .execute()
    )

    logger.info(profile_resp)
    if not profile_resp.data:
        raise HTTPException(status_code=400, detail=profile_resp.error.message)
    return {"user": user, "profile": profile_resp.data}

@router.patch("/user")
def update_profile(updates: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    update_data = updates.dict(exclude_unset=True)
    profile_resp = (
        supabase_admin
        .from_("user_profiles")
        .update(update_data)
        .eq("id", user["sub"])
        .execute()
    )
    # Check if the update returned data; if not, consider it a failure.
    if not profile_resp.data:
        raise HTTPException(status_code=400, detail="Profile update failed.")
    return profile_resp.data

@router.post("/user/avatar")
async def upload_avatar(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """
    Upload an avatar file to Supabase Storage and update the user's profile.
    """
    # Generate a unique file path
    file_ext = file.filename.split(".")[-1]
    file_path = f"{user['id']}/{uuid.uuid4()}.{file_ext}"
    
    # Read the file bytes
    file_bytes = await file.read()

    # Upload the file to the "profile-pictures" bucket
    upload_response = supabase_admin.storage.from_("profile-pictures").upload(file_path, file_bytes)
    if upload_response.error:
        raise HTTPException(status_code=400, detail=upload_response.error.message)
    
    # Get the public URL for the uploaded file
    public_url_response = supabase_admin.storage.from_("profile-pictures").get_public_url(file_path)
    public_url = public_url_response.data.get("publicUrl")
    
    # Update the user profile with the new avatar URL
    update_resp = (
        supabase_admin
        .from_("user_profiles")
        .update({"avatar_url": public_url})
        .eq("id", user["sub"])
        .select()
        .single()
        .execute()
    )
    if update_resp.error:
        raise HTTPException(status_code=400, detail=update_resp.error.message)
    
    return {"avatar_url": public_url}

@router.post("/signout")
def sign_out(user: dict = Depends(get_current_user)):
    """
    Sign out the current user.
    This endpoint can also be used to perform server-side cleanup if needed.
    """
    # Note: With Supabase, sign-out is typically handled client-side.
    # Optionally, you can implement token revocation or server-side session cleanup here.
    return {"message": "Signed out successfully"}
