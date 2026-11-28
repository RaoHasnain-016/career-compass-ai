from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.models.career_model import Career
from app.models.recommendation_model import Recommendation, RecommendationFeedback
from app.models.saved_career_model import SavedCareer
from app.schemas.recommendation_schema import RecommendationFeedbackRequest
from app.services.career_ranker import personalize_recommendations, rank_recommendations, ranker_configured
from app.services.recommendation_service import generate_recommendation_analysis
from app.services.student_updates_service import record_student_update
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)

Ranking = Literal["rules", "model", "personalized"]


def get_current_db_user(firebase_user, db: Session):
    firebase_uid = firebase_user.get("uid")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please login first."
        )

    return user


def recommendation_to_dict(recommendation: Recommendation):
    career = recommendation.career

    return {
        "recommendation_id": str(recommendation.recommendation_id),
        "career_id": str(career.career_id),

        "title": career.title,
        "field": career.field,
        "overview": career.overview,
        "required_education": career.required_education,
        "required_skills": career.required_skills or [],
        "required_subjects": career.required_subjects or [],
        "future_scope": career.future_scope,
        "difficulty_level": career.difficulty_level,

        "match_score": float(recommendation.match_score),
        "confidence_level": recommendation.confidence_level,
        "eligibility_status": recommendation.eligibility_status,

        "matched_interests": recommendation.matched_interests or [],
        "matched_skills": recommendation.matched_skills or [],
        "matched_subjects": recommendation.matched_subjects or [],

        "missing_skills": recommendation.missing_skills or [],
        "missing_subjects": recommendation.missing_subjects or [],

        "explanation": recommendation.explanation,
        "improvement_advice": recommendation.improvement_advice,
    }


def get_saved_ranking_preferences(db, user_id):
    return (
        db.query(SavedCareer.career_id, Career.field)
        .select_from(SavedCareer)
        .join(Career, SavedCareer.career_id == Career.career_id)
        .filter(SavedCareer.user_id == user_id, Career.status.is_(True))
        .all()
    )


def get_ranking_feedback(db, user_id):
    return dict(
        db.query(RecommendationFeedback.career_id, RecommendationFeedback.feedback)
        .filter(RecommendationFeedback.user_id == user_id)
        .all()
    )


def ranked_payload(recommendations, profile, ranking, saved_careers=(), feedback=None):
    model_available = ranker_configured()
    feedback = feedback or {}
    ordered, source = recommendations, "rules"
    reasons = {}
    if ranking == "model" and model_available:
        ordered, source = rank_recommendations(profile, recommendations)
    elif ranking == "personalized" and (saved_careers or feedback):
        ordered, reasons = personalize_recommendations(recommendations, saved_careers, feedback)
        if reasons:
            source = "personalized"

    rows = [
        {**recommendation_to_dict(item), "feedback": feedback.get(item.career_id)}
        for item in ordered
    ]
    if source == "trained":
        for rank, row in enumerate(rows, 1):
            row["model_rank"] = rank
    elif reasons:
        for item, row in zip(ordered, rows):
            if item.career_id in reasons:
                row["personalization_reason"] = reasons[item.career_id]
    return {
        "ranking_source": source,
        "model_ranking_available": model_available,
        "recommendations": rows,
    }


@router.put("/{career_id}/feedback")
def set_recommendation_feedback(
    career_id: UUID,
    request: RecommendationFeedbackRequest,
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
):
    user = get_current_db_user(firebase_user, db)
    if request.feedback is None:
        db.query(RecommendationFeedback).filter(
            RecommendationFeedback.user_id == user.user_id,
            RecommendationFeedback.career_id == career_id,
        ).delete(synchronize_session=False)
    else:
        recommendation = (
            db.query(Recommendation.career_id)
            .join(Career, Recommendation.career_id == Career.career_id)
            .filter(
                Recommendation.user_id == user.user_id,
                Recommendation.career_id == career_id,
                Career.status.is_(True),
            )
            .first()
        )
        if recommendation is None:
            raise HTTPException(status_code=404, detail="Active recommendation not found.")
        insert = sqlite_insert if db.get_bind().dialect.name == "sqlite" else postgres_insert
        statement = insert(RecommendationFeedback).values(
            user_id=user.user_id, career_id=career_id, feedback=request.feedback,
        )
        db.execute(statement.on_conflict_do_update(
            index_elements=[RecommendationFeedback.user_id, RecommendationFeedback.career_id],
            set_={"feedback": statement.excluded.feedback},
        ))
    db.commit()
    return {"career_id": str(career_id), "feedback": request.feedback}


@router.post("/generate")
def generate_recommendations(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
    ranking: Ranking = "rules",
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

    careers = db.query(Career).filter(Career.status == True).all()

    if not careers:
        raise HTTPException(
            status_code=404,
            detail="No career records found."
        )

    # Delete old recommendations before generating fresh results
    db.query(Recommendation).filter(
        Recommendation.user_id == user.user_id
    ).delete()

    generated_recommendations = []

    for career in careers:
        analysis = generate_recommendation_analysis(profile, career)

        recommendation = Recommendation(
            user_id=user.user_id,
            career_id=career.career_id,

            match_score=analysis["score"],
            confidence_level=analysis["confidence_level"],
            eligibility_status=analysis["eligibility_status"],

            matched_interests=analysis["matched_interests"],
            matched_skills=analysis["matched_skills"],
            matched_subjects=analysis["matched_subjects"],

            missing_skills=analysis["missing_skills"],
            missing_subjects=analysis["missing_subjects"],

            explanation=analysis["explanation"],
            improvement_advice=analysis["improvement_advice"],
        )

        db.add(recommendation)
        generated_recommendations.append(recommendation)

    record_student_update(
        db, user.user_id, category="recommendations", title="New career recommendations",
        summary="Your recommendations were refreshed. Open them to compare careers and review your learning gaps.",
        url="/recommendations",
    )
    db.commit()

    for recommendation in generated_recommendations:
        db.refresh(recommendation)

    generated_recommendations.sort(
        key=lambda item: float(item.match_score),
        reverse=True
    )
    saved_careers = get_saved_ranking_preferences(db, user.user_id) if ranking == "personalized" else ()

    return {
        "message": "Recommendations generated successfully",
        "total_careers_analyzed": len(careers),
        **ranked_payload(generated_recommendations, profile, ranking, saved_careers, get_ranking_feedback(db, user.user_id)),
    }


@router.get("/me")
def get_my_recommendations(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
    ranking: Ranking = "rules",
):
    user = get_current_db_user(firebase_user, db)

    recommendations = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.career))
        .filter(Recommendation.user_id == user.user_id)
        .order_by(Recommendation.match_score.desc())
        .all()
    )

    profile = None
    if recommendations and ranking == "model" and ranker_configured():
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.user_id).first()
    saved_careers = get_saved_ranking_preferences(db, user.user_id) if recommendations and ranking == "personalized" else ()
    feedback = get_ranking_feedback(db, user.user_id) if recommendations else {}
    return ranked_payload(recommendations, profile, ranking, saved_careers, feedback)
