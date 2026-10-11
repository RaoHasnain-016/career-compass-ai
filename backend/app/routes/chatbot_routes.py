from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.models.career_model import Career
from app.models.recommendation_model import Recommendation
from app.models.roadmap_model import RoadmapStage
from app.models.resource_model import LearningResource
from app.models.video_resource_model import VideoResource
from app.models.saved_career_model import SavedCareer
from app.models.chat_model import ChatMessage
from app.schemas.chatbot_schema import ChatbotRequest
from app.services.chatbot_service import (
    ChatbotServiceError,
    build_chatbot_context,
    ask_career_chatbot,
)
from app.services.resource_service import find_missing_skills
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/chatbot",
    tags=["AI Chatbot"]
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


@router.post("/ask")
def ask_chatbot(
    request: ChatbotRequest,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message is required."
        )

    user = get_current_db_user(firebase_user, db)

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.user_id)
        .first()
    )

    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.user_id)
        .order_by(Recommendation.match_score.desc())
        .limit(3)
        .all()
    )

    selected_career = None
    roadmap_stages = []
    learning_resources = []
    video_courses = []

    if request.career_id:
        try:
            career_uuid = UUID(request.career_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid career_id format."
            )

        selected_career = (
            db.query(Career)
            .filter(Career.career_id == career_uuid)
            .first()
        )

        if not selected_career:
            raise HTTPException(
                status_code=404,
                detail="Selected career not found."
            )

        roadmap_stages = (
            db.query(RoadmapStage)
            .filter(
                RoadmapStage.career_id == selected_career.career_id,
                RoadmapStage.status == True
            )
            .order_by(RoadmapStage.stage_order.asc())
            .all()
        )

        missing_skills = []

        if profile:
            missing_skills = find_missing_skills(
                student_skills=profile.skills,
                required_skills=selected_career.required_skills
            )

        all_resources = (
            db.query(LearningResource)
            .filter(
                LearningResource.status == True,
                LearningResource.is_free == True
            )
            .limit(15)
            .all()
        )

        if missing_skills:
            lower_missing = [skill.lower() for skill in missing_skills]

            learning_resources = [
                resource
                for resource in all_resources
                if resource.skill and resource.skill.lower() in lower_missing
            ][:5]
        else:
            learning_resources = all_resources[:5]

        video_courses = (
            db.query(VideoResource)
            .filter(
                VideoResource.career_field == selected_career.field,
                VideoResource.status == True
            )
            .limit(5)
            .all()
        )

    saved_careers = (
        db.query(SavedCareer)
        .filter(SavedCareer.user_id == user.user_id)
        .all()
    )

    chat_history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(3)
        .all()
    )

    context = build_chatbot_context(
        user=user,
        profile=profile,
        recommendations=recommendations,
        selected_career=selected_career,
        roadmap_stages=roadmap_stages,
        learning_resources=learning_resources,
        video_courses=video_courses,
        saved_careers=saved_careers,
        chat_history=list(reversed(chat_history)),
    )

    try:
        ai_response = ask_career_chatbot(
            user_message=request.message.strip(),
            context=context
        )
    except ChatbotServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error

    chat_message = ChatMessage(
        user_id=user.user_id,
        question=request.message.strip(),
        response=ai_response,
    )

    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)

    return {
        "message_id": str(chat_message.message_id),
        "question": chat_message.question,
        "response": chat_message.response,
    }


@router.get("/history")
def get_chat_history(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.user_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return {
        "history": [
            {
                "message_id": str(message.message_id),
                "question": message.question,
                "response": message.response,
                "created_at": message.created_at,
            }
            for message in messages
        ]
    }
