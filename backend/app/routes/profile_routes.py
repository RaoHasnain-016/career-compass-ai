from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.schemas.profile_schema import StudentProfileCreate, StudentProfileUpdate
from app.services.student_updates_service import record_student_update
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


def profile_field_changed(profile, field, value):
    current = getattr(profile, field)
    if current is None or value is None:
        return current != value
    if field == "selected_career_id":
        return str(current) != str(value)
    if field == "marks_cgpa":
        return float(current) != value
    return current != value


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
        selected_career_id=profile_data.selected_career_id,
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
    record_student_update(
        db, user.user_id, category="profile", title="Student profile created",
        summary="Your education and interests are ready to use for personalised guidance.", url="/profile-setup",
    )
    db.commit()
    db.refresh(profile)

    return {
        "message": "Student profile created successfully",
        "profile": {
            "profile_id": str(profile.profile_id),
            "user_id": str(profile.user_id),
            "age": profile.age,
            "country": profile.country,
            "selected_career_id": str(profile.selected_career_id) if profile.selected_career_id else None,
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
        "selected_career_id": str(profile.selected_career_id) if profile.selected_career_id else None,
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
    changed = {key for key, value in update_data.items() if profile_field_changed(profile, key, value)}

    for key, value in update_data.items():
        setattr(profile, key, value)

    if "selected_career_id" in changed:
        record_student_update(
            db, user.user_id, category="recommendations", title="Active career updated",
            summary="Your roadmap and learning priorities reflect your active career choice.", url="/skill-gap",
        )
    if changed - {"selected_career_id"}:
        record_student_update(
            db, user.user_id, category="profile", title="Student profile updated",
            summary="Your profile was saved. Generate new recommendations to reflect these changes.", url="/recommendations",
        )

    db.commit()
    db.refresh(profile)

    return {
        "message": "Student profile updated successfully",
        "profile": {
            "profile_id": str(profile.profile_id),
            "user_id": str(profile.user_id),
            "age": profile.age,
            "country": profile.country,
            "selected_career_id": str(profile.selected_career_id) if profile.selected_career_id else None,
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
