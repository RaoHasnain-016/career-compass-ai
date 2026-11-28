import os
from types import SimpleNamespace
from uuid import UUID

from anyio import from_thread
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.models.career_model import Career
from app.models.recommendation_model import Recommendation
from app.models.roadmap_model import RoadmapStage
from app.models.resource_model import LearningResource
from app.models.saved_career_model import SavedCareer
from app.models.chat_model import ChatMessage
from app.schemas.chatbot_schema import ChatbotRequest
from app.services.casual_chat_service import answer_casual_chat
from app.services.career_knowledge_base import answer_from_knowledge_base
from app.services.chatbot_analysis_service import answer_profile_analysis
from app.services.chatbot_service import (
    CHATBOT_PROVIDER,
    ChatbotReply,
    ChatbotServiceError,
    answer_from_saved_guidance,
    build_chatbot_context,
    ask_career_chatbot,
)
from app.services.career_ranker import rank_recommendations, ranker_configured
from app.services.chatbot_knowledge_service import (
    empty_evidence, evidence_only_answer, knowledge_topic, retrieve_chat_evidence,
)
from app.services.general_chat_service import answer_general_question
from app.services.local_chat_service import LocalChatError, ask_local_chatbot, local_chat_pilot_available
from app.services.resource_service import find_missing_skills
from app.services.student_updates_service import UpdateAudience, academic_fields, education_stage, load_audience
from app.services.video_learning_service import recommend_video_courses
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


def active_career(db, career_id):
    return (
        db.query(Career)
        .filter(Career.career_id == career_id, Career.status.is_(True))
        .first()
    )


def save_chat_reply(db, user_id, question, reply, evidence=None):
    message = ChatMessage(user_id=user_id, question=question, response=str(reply))
    db.add(message)
    db.commit()
    db.refresh(message)

    result = {
        "message_id": str(message.message_id),
        "question": message.question,
        "response": message.response,
    }
    if mode := getattr(reply, "mode", None):
        result["reply_mode"] = mode
    if evidence:
        result["sources"] = evidence["items"]
        result["source_status"] = evidence["status"]
        result["sources_checked_at"] = evidence["checked_at"]
    return result


@router.post("/ask")
def ask_chatbot(
    request: ChatbotRequest,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    question = request.message.strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Message is required."
        )

    user = get_current_db_user(firebase_user, db)
    user_id = user.user_id

    selected_career = None
    if request.career_id:
        try:
            career_uuid = UUID(request.career_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid career_id format.") from None
        selected_career = active_career(db, career_uuid)
        if selected_career is None:
            raise HTTPException(status_code=404, detail="Selected career not found.")

    casual = answer_casual_chat(question)
    if casual is not None:
        return save_chat_reply(db, user_id, question, ChatbotReply(casual, "casual_chat"))
    if reference := answer_from_knowledge_base(question):
        reply, evidence = reference
        return save_chat_reply(db, user_id, question, ChatbotReply(reply, "knowledge_base"), evidence)
    if (general := answer_general_question(question)) is not None:
        return save_chat_reply(db, user_id, question, ChatbotReply(general, "general_guidance"))


    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == user.user_id)
        .first()
    )

    recommendation_query = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.user_id)
        .order_by(Recommendation.match_score.desc())
    )
    local_chat = CHATBOT_PROVIDER == "local"
    if local_chat and ranker_configured() and profile is not None:
        ranked, _ = rank_recommendations(profile, recommendation_query.all())
        recommendations = ranked[:3]
    else:
        recommendations = recommendation_query.limit(3).all()

    roadmap_stages = []
    learning_resources = []
    video_courses = []

    if selected_career is None and profile is not None:
        career_uuid = profile.selected_career_id
        if career_uuid is None and recommendations:
            career_uuid = recommendations[0].career_id
        if career_uuid is not None:
            selected_career = active_career(db, career_uuid)

    if selected_career:
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

        resource_query = (
            db.query(LearningResource)
            .filter(
                LearningResource.status == True,
                LearningResource.is_free == True
            )
        )

        if missing_skills:
            resource_query = resource_query.filter(func.lower(LearningResource.skill).in_(missing_skills))
        else:
            resource_query = resource_query.filter(LearningResource.career_field == selected_career.field)
        learning_resources = resource_query.order_by(LearningResource.title).limit(5).all()

        videos = recommend_video_courses(
            db, selected_career.title, selected_career.field,
            selected_career.required_skills or [], missing_skills, live=False,
        )
        video_courses = [SimpleNamespace(**video) for video in videos[:3]]

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

    pilot_requested = request.mode == "pilot"
    pilot_available = pilot_requested and local_chat_pilot_available()
    live_enabled = os.getenv("CHATBOT_LIVE_KNOWLEDGE", "").strip().lower() in {"true", "1"}
    topic = knowledge_topic(question) if local_chat or live_enabled or pilot_available else None
    audience = None
    if topic and live_enabled and profile is not None:
        audience = load_audience(db, user_id)
        if request.career_id and selected_career:
            audience = UpdateAudience(
                audience.stage, audience.country, tuple(academic_fields(selected_career.field)), selected_career.title,
            )
    stage = education_stage(profile.academic_level) if profile is not None else "exploring"

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

    # Return the read connection before any publisher or model request.
    db.rollback()

    evidence = None
    try:
        if topic:
            evidence = (
                from_thread.run(retrieve_chat_evidence, topic, audience) if audience else
                empty_evidence(topic, stage, "offline" if profile is not None else "profile_needed")
            )
            ai_response = ChatbotReply(evidence_only_answer(evidence, question), "official_sources")
        elif (analysis := answer_profile_analysis(question, context)) is not None:
            ai_response = ChatbotReply(analysis, "profile_analysis")
        elif pilot_requested:
            if not pilot_available or len(question) > 1600:
                raise LocalChatError("The conversation pilot is unavailable for this request.")
            answer = ask_local_chatbot(request.message, context)
            ai_response = ChatbotReply(answer, "conversation_pilot")
        else:
            ai_response = answer_from_saved_guidance(question, context)
            if ai_response is None:
                ai_response = ask_career_chatbot(user_message=question, context=context)
    except (ChatbotServiceError, LocalChatError):
        ai_response = answer_from_saved_guidance(question, context, fallback=True)

    return save_chat_reply(db, user_id, question, ai_response, evidence)


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
        "pilot_available": local_chat_pilot_available(),
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
