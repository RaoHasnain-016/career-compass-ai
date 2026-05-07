from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.profile_model import StudentProfile
from app.models.career_model import Career
from app.models.recommendation_model import Recommendation
from app.services.recommendation_service import generate_recommendation_analysis
from app.utils.auth_dependency import get_current_firebase_user

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
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


@router.post("/generate")
def generate_recommendations(
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
    db.commit()

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

    db.commit()

    for recommendation in generated_recommendations:
        db.refresh(recommendation)

    generated_recommendations.sort(
        key=lambda item: float(item.match_score),
        reverse=True
    )

    return {
        "message": "Recommendations generated successfully",
        "total_careers_analyzed": len(careers),
        "recommendations": [
            recommendation_to_dict(recommendation)
            for recommendation in generated_recommendations
        ]
    }


@router.get("/me")
def get_my_recommendations(
    firebase_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db)
):
    user = get_current_db_user(firebase_user, db)

    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.user_id)
        .order_by(Recommendation.match_score.desc())
        .all()
    )

    return {
        "recommendations": [
            recommendation_to_dict(recommendation)
            for recommendation in recommendations
        ]
    }