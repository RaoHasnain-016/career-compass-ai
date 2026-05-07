from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.models.career_model import Career
from app.models.resource_model import LearningResource
from app.models.video_resource_model import VideoResource
from app.schemas.resource_schema import LearningResourceCreate, LearningResourceUpdate
from app.services.resource_service import find_missing_skills, is_resource_relevant
from app.services.youtube_service import search_youtube_videos
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


def video_to_dict(video: VideoResource):
    return {
        "video_resource_id": str(video.video_resource_id),
        "youtube_video_id": video.youtube_video_id,
        "title": video.title,
        "channel_title": video.channel_title,
        "thumbnail_url": video.thumbnail_url,
        "video_url": video.video_url,
        "skill": video.skill,
        "career_field": video.career_field,
        "difficulty": video.difficulty,
        "source": video.source,
        "is_free": video.is_free,
        "status": video.status,
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

    recommended_videos = []

    for skill in missing_skills[:5]:
        cached_videos = (
            db.query(VideoResource)
            .filter(
                VideoResource.skill.ilike(skill),
                VideoResource.career_field == career.field,
                VideoResource.status == True,
            )
            .limit(5)
            .all()
        )

        if cached_videos:
            recommended_videos.extend(cached_videos)
            continue

        query = f"{skill} full course beginner {career.title}"

        youtube_results = search_youtube_videos(
            query=query,
            max_results=5
        )

        for item in youtube_results:
            existing_video = (
                db.query(VideoResource)
                .filter(
                    VideoResource.youtube_video_id == item["youtube_video_id"]
                )
                .first()
            )

            if existing_video:
                recommended_videos.append(existing_video)
                continue

            video = VideoResource(
                youtube_video_id=item["youtube_video_id"],
                title=item["title"],
                channel_title=item["channel_title"],
                thumbnail_url=item["thumbnail_url"],
                video_url=item["video_url"],
                skill=skill,
                career_field=career.field,
                difficulty="Beginner",
                source="YouTube",
                is_free=True,
                status=True,
            )

            db.add(video)
            db.commit()
            db.refresh(video)

            recommended_videos.append(video)

    return {
        "career": {
            "career_id": str(career.career_id),
            "title": career.title,
            "field": career.field,
        },
        "student_skills": profile.skills or [],
        "required_skills": career.required_skills or [],
        "missing_skills": missing_skills,
        "video_courses": [
            video_to_dict(video)
            for video in recommended_videos
        ]
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