from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.career_model import Career
from app.models.saved_career_model import SavedCareer
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/saved-careers",
    tags=["Saved Careers"]
)


def get_current_db_user(firebase_user, db: Session):
    firebase_uid = firebase_user.get("uid")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please login first."
        )

    return user


def saved_career_to_dict(saved_career: SavedCareer):
    career = saved_career.career

    return {
        "saved_id": str(saved_career.saved_id),
        "career_id": str(career.career_id),
        "title": career.title,
        "field": career.field,
        "overview": career.overview,
        "required_education": career.required_education,
        "required_skills": career.required_skills or [],
        "required_subjects": career.required_subjects or [],
        "future_scope": career.future_scope,
        "difficulty_level": career.difficulty_level,
        "created_at": saved_career.created_at,
    }


@router.post("/{career_id}")
def save_career(
    career_id: UUID,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    career = db.query(Career).filter(Career.career_id == career_id).first()

    if not career:
        raise HTTPException(
            status_code=404,
            detail="Career not found"
        )

    existing_saved = (
        db.query(SavedCareer)
        .filter(
            SavedCareer.user_id == user.user_id,
            SavedCareer.career_id == career_id
        )
        .first()
    )

    if existing_saved:
        raise HTTPException(
            status_code=400,
            detail="Career already saved"
        )

    saved_career = SavedCareer(
        user_id=user.user_id,
        career_id=career_id
    )

    db.add(saved_career)
    db.commit()
    db.refresh(saved_career)

    return {
        "message": "Career saved successfully",
        "saved_career": saved_career_to_dict(saved_career)
    }


@router.get("")
def get_saved_careers(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    saved_careers = (
        db.query(SavedCareer)
        .filter(SavedCareer.user_id == user.user_id)
        .all()
    )

    return {
        "saved_careers": [
            saved_career_to_dict(saved_career)
            for saved_career in saved_careers
        ]
    }


@router.delete("/{career_id}")
def remove_saved_career(
    career_id: UUID,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    saved_career = (
        db.query(SavedCareer)
        .filter(
            SavedCareer.user_id == user.user_id,
            SavedCareer.career_id == career_id
        )
        .first()
    )

    if not saved_career:
        raise HTTPException(
            status_code=404,
            detail="Saved career not found"
        )

    db.delete(saved_career)
    db.commit()

    return {
        "message": "Saved career removed successfully"
    }