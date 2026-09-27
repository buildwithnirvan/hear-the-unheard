from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.database.mongo import get_db
from app.models.user import new_user_document

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, description="Minimum 8 characters")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Database = Depends(get_db)):
    document = new_user_document(
        email=body.email, display_name=body.display_name, hashed_password=hash_password(body.password)
    )
    try:
        db.users.insert_one(document)
    except DuplicateKeyError:
        # The real guarantee against a duplicate email is the unique
        # index on `email` (see app/database/mongo.py:ensure_indexes) —
        # this catches the race, it isn't the only thing preventing it.
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    token = create_access_token(subject=document["_id"], role=document["role"])
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db)):
    # OAuth2PasswordRequestForm's "username" field carries the email here.
    user = db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="This account has been deactivated")

    token = create_access_token(subject=user["_id"], role=user["role"])
    return TokenResponse(access_token=token)


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "display_name": current_user["display_name"],
        "role": current_user["role"],
    }
