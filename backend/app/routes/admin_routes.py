from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.models.career_model import Career
from app.models.resource_model import LearningResource
from app.models.roadmap_model import RoadmapStage
from app.models.recommendation_model import Recommendation
from app.models.saved_career_model import SavedCareer
from app.models.chat_model import ChatMessage
from app.models.video_resource_model import VideoResource
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
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


def require_admin(user: User):
    if user.role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required."
        )


@router.get("/dashboard")
def admin_dashboard(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)
    require_admin(user)

    total_users = db.query(User).count()
    total_students = db.query(User).filter(User.role == "student").count()
    total_admins = db.query(User).filter(User.role == "admin").count()
    total_profiles = db.query(StudentProfile).count()
    total_careers = db.query(Career).filter(Career.status == True).count()
    total_resources = db.query(LearningResource).filter(LearningResource.status == True).count()
    total_video_resources = db.query(VideoResource).filter(VideoResource.status == True).count()
    total_roadmap_stages = db.query(RoadmapStage).filter(RoadmapStage.status == True).count()
    total_recommendations = db.query(Recommendation).count()
    total_saved_careers = db.query(SavedCareer).count()
    total_chat_messages = db.query(ChatMessage).count()

    popular_careers = (
        db.query(
            Career.title,
            Career.field,
            func.count(Recommendation.recommendation_id).label("recommendation_count")
        )
        .join(Recommendation, Recommendation.career_id == Career.career_id)
        .group_by(Career.title, Career.field)
        .order_by(func.count(Recommendation.recommendation_id).desc())
        .limit(5)
        .all()
    )

    return {
        "stats": {
            "total_users": total_users,
            "total_students": total_students,
            "total_admins": total_admins,
            "total_profiles": total_profiles,
            "total_careers": total_careers,
            "total_resources": total_resources,
            "total_video_resources": total_video_resources,
            "total_roadmap_stages": total_roadmap_stages,
            "total_recommendations": total_recommendations,
            "total_saved_careers": total_saved_careers,
            "total_chat_messages": total_chat_messages,
        },
        "popular_careers": [
            {
                "title": career.title,
                "field": career.field,
                "recommendation_count": career.recommendation_count,
            }
            for career in popular_careers
        ]
    }


@router.get("/users")
def get_users(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)
    require_admin(user)

    users = db.query(User).order_by(User.created_at.desc()).all()

    return {
        "users": [
            {
                "user_id": str(item.user_id),
                "firebase_uid": item.firebase_uid,
                "full_name": item.full_name,
                "email": item.email,
                "role": item.role,
                "photo_url": item.photo_url,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in users
        ]
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    role: str,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    current_user = get_current_db_user(firebase_user, db)
    require_admin(current_user)

    if role.lower() not in ["student", "admin"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be student or admin."
        )

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    user.role = role.lower()
    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully",
        "user": {
            "user_id": str(user.user_id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
        }
    }


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    status: str,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    current_user = get_current_db_user(firebase_user, db)
    require_admin(current_user)

    if status.lower() not in ["active", "blocked", "disabled"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be active, blocked, or disabled."
        )

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    user.status = status.lower()
    db.commit()
    db.refresh(user)

    return {
        "message": "User status updated successfully",
        "user": {
            "user_id": str(user.user_id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
        }
    }