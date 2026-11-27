from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.models.career_model import Career
from app.models.resource_model import LearningResource
from app.schemas.resource_schema import LearningResourceCreate, LearningResourceUpdate
from app.services.resource_service import find_missing_skills, is_resource_relevant
from app.services.video_learning_service import recommend_video_courses
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/resources",
    tags=["Learning Resources"]
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


def resource_to_dict(resource: LearningResource):
    return {
        "resource_id": str(resource.resource_id),
        "title": resource.title,
        "platform": resource.platform,
        "url": resource.url,
        "skill": resource.skill,
        "career_field": resource.career_field,
        "difficulty": resource.difficulty,
        "resource_type": resource.resource_type,
        "description": resource.description,
        "is_free": resource.is_free,
        "status": resource.status,
    }


@router.post("")
def create_resource(
    resource_data: LearningResourceCreate,
    db: Session = Depends(get_db)
):
    resource = LearningResource(
        title=resource_data.title,
        platform=resource_data.platform,
        url=resource_data.url,
        skill=resource_data.skill,
        career_field=resource_data.career_field,
        difficulty=resource_data.difficulty,
        resource_type=resource_data.resource_type,
        description=resource_data.description,
        is_free=resource_data.is_free,
        status=resource_data.status,
    )

    db.add(resource)
    db.commit()
    db.refresh(resource)

    return {
        "message": "Learning resource created successfully",
        "resource": resource_to_dict(resource)
    }


@router.get("")
def get_resources(db: Session = Depends(get_db)):
    resources = (
        db.query(LearningResource)
        .filter(LearningResource.status == True)
        .all()
    )

    return {
        "resources": [resource_to_dict(resource) for resource in resources]
    }


@router.get("/recommended/{career_id}")
def get_recommended_resources(
    career_id: UUID,
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
            detail="Student profile not found. Please complete your profile first."
        )

    career = db.query(Career).filter(Career.career_id == career_id).first()

    if not career:
        raise HTTPException(
            status_code=404,
            detail="Career not found"
        )

    missing_skills = find_missing_skills(
        student_skills=profile.skills,
        required_skills=career.required_skills
    )

    resources = (
        db.query(LearningResource)
        .filter(
            LearningResource.status == True,
            LearningResource.is_free == True
        )
        .all()
    )

    recommended_resources = [
        resource
        for resource in resources
        if is_resource_relevant(
            resource=resource,
            missing_skills=missing_skills,
            career_field=career.field
        )
    ]

    return {
        "career": {
            "career_id": str(career.career_id),
            "title": career.title,
            "field": career.field,
        },
        "student_skills": profile.skills or [],
        "required_skills": career.required_skills or [],
        "missing_skills": missing_skills,
        "recommended_resources": [
            resource_to_dict(resource)
            for resource in recommended_resources
        ]
    }


@router.get("/videos/{career_id}")
def get_recommended_video_courses(
    career_id: UUID,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
    live: bool = True,
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
            detail="Student profile not found. Please complete your profile first."
        )

    career = db.query(Career).filter(Career.career_id == career_id, Career.status.is_(True)).first()

    if not career:
        raise HTTPException(
            status_code=404,
            detail="Career not found"
        )

    career_info = {
        "career_id": str(career.career_id),
        "title": career.title,
        "field": career.field,
    }
    student_skills = profile.skills or []
    required_skills = career.required_skills or []
    missing_skills = find_missing_skills(student_skills, required_skills)
    return {
        "career": career_info,
        "student_skills": student_skills,
        "required_skills": required_skills,
        "missing_skills": missing_skills,
        "video_courses": recommend_video_courses(
            db, career_info["title"], career_info["field"], required_skills, missing_skills, live=live,
        ),
    }


@router.put("/{resource_id}")
def update_resource(
    resource_id: UUID,
    resource_data: LearningResourceUpdate,
    db: Session = Depends(get_db)
):
    resource = (
        db.query(LearningResource)
        .filter(LearningResource.resource_id == resource_id)
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Learning resource not found"
        )

    update_data = resource_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(resource, key, value)

    db.commit()
    db.refresh(resource)

    return {
        "message": "Learning resource updated successfully",
        "resource": resource_to_dict(resource)
    }


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: UUID,
    db: Session = Depends(get_db)
):
    resource = (
        db.query(LearningResource)
        .filter(LearningResource.resource_id == resource_id)
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Learning resource not found"
        )

    resource.status = False

    db.commit()
    db.refresh(resource)

    return {
        "message": "Learning resource deleted successfully"
    }
