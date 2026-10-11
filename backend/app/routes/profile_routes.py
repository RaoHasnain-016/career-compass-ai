from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.schemas.profile_schema import StudentProfileCreate, StudentProfileUpdate
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/student",
    tags=["Student Profile"]
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


@router.post("/profile")
def create_profile(
    profile_data: StudentProfileCreate,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    existing_profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.user_id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists. Use PUT /student/profile to update it."
        )

    profile = StudentProfile(
        user_id=user.user_id,
        age=profile_data.age,
        country=profile_data.country,
        academic_level=profile_data.academic_level,
        class_degree=profile_data.class_degree,
        marks_cgpa=profile_data.marks_cgpa,
        favorite_subjects=profile_data.favorite_subjects,
        weak_subjects=profile_data.weak_subjects,
        interests=profile_data.interests,
        skills=profile_data.skills,
        study_preference=profile_data.study_preference,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "message": "Student profile created successfully",
        "profile": {
            "profile_id": str(profile.profile_id),
            "user_id": str(profile.user_id),
            "age": profile.age,
            "country": profile.country,
            "academic_level": profile.academic_level,
            "class_degree": profile.class_degree,
            "marks_cgpa": float(profile.marks_cgpa) if profile.marks_cgpa else None,
            "favorite_subjects": profile.favorite_subjects,
            "weak_subjects": profile.weak_subjects,
            "interests": profile.interests,
            "skills": profile.skills,
            "study_preference": profile.study_preference,
        }
    }


@router.get("/profile")
def get_profile(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found."
        )

    return {
        "profile_id": str(profile.profile_id),
        "user_id": str(profile.user_id),
        "age": profile.age,
        "country": profile.country,
        "academic_level": profile.academic_level,
        "class_degree": profile.class_degree,
        "marks_cgpa": float(profile.marks_cgpa) if profile.marks_cgpa else None,
        "favorite_subjects": profile.favorite_subjects,
        "weak_subjects": profile.weak_subjects,
        "interests": profile.interests,
        "skills": profile.skills,
        "study_preference": profile.study_preference,
    }


@router.put("/profile")
def update_profile(
    profile_data: StudentProfileUpdate,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found. Please create profile first."
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return {
        "message": "Student profile updated successfully",
        "profile": {
            "profile_id": str(profile.profile_id),
            "user_id": str(profile.user_id),
            "age": profile.age,
            "country": profile.country,
            "academic_level": profile.academic_level,
            "class_degree": profile.class_degree,
            "marks_cgpa": float(profile.marks_cgpa) if profile.marks_cgpa else None,
            "favorite_subjects": profile.favorite_subjects,
            "weak_subjects": profile.weak_subjects,
            "interests": profile.interests,
            "skills": profile.skills,
            "study_preference": profile.study_preference,
        }
    }
