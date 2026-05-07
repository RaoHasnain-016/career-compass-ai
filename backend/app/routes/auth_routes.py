from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class FirebaseLoginRequest(BaseModel):
    full_name: str | None = None


@router.post("/firebase-login")
def firebase_login(
    body: FirebaseLoginRequest | None = None,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    firebase_uid = firebase_user.get("uid")
    email = firebase_user.get("email")
    token_name = firebase_user.get("name")
    photo_url = firebase_user.get("picture")

    full_name = (
        body.full_name
        if body and body.full_name
        else token_name
        if token_name
        else "Student"
    )

    if not firebase_uid or not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid Firebase user data"
        )

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        user = User(
            firebase_uid=firebase_uid,
            full_name=full_name,
            email=email,
            role="student",
            photo_url=photo_url,
            status="active"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.full_name = full_name
        user.email = email
        user.photo_url = photo_url
        db.commit()
        db.refresh(user)

    return {
        "message": "Firebase login successful",
        "user": {
            "user_id": str(user.user_id),
            "firebase_uid": user.firebase_uid,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "photo_url": user.photo_url,
            "status": user.status
        }
    }


@router.get("/me")
def me(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    firebase_uid = firebase_user.get("uid")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found in database. Please login first."
        )

    return {
        "user_id": str(user.user_id),
        "firebase_uid": user.firebase_uid,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "photo_url": user.photo_url,
        "status": user.status
    }