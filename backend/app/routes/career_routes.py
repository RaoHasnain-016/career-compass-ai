from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.career_model import Career
from app.schemas.career_schema import CareerCreate, CareerUpdate

router = APIRouter(
    prefix="/careers",
    tags=["Careers"]
)


def career_to_dict(career: Career):
    return {
        "career_id": str(career.career_id),
        "title": career.title,
        "field": career.field,
        "overview": career.overview,
        "required_education": career.required_education,
        "required_skills": career.required_skills,
        "required_subjects": career.required_subjects,
        "related_interests": career.related_interests,
        "minimum_marks": float(career.minimum_marks) if career.minimum_marks is not None else 0,
        "future_scope": career.future_scope,
        "difficulty_level": career.difficulty_level,
        "status": career.status,
    }


@router.post("")
def create_career(
    career_data: CareerCreate,
    db: Session = Depends(get_db)
):
    career = Career(
        title=career_data.title,
        field=career_data.field,
        overview=career_data.overview,
        required_education=career_data.required_education,
        required_skills=career_data.required_skills,
        required_subjects=career_data.required_subjects,
        related_interests=career_data.related_interests,
        minimum_marks=career_data.minimum_marks,
        future_scope=career_data.future_scope,
        difficulty_level=career_data.difficulty_level,
        status=career_data.status,
    )

    db.add(career)
    db.commit()
    db.refresh(career)

    return {
        "message": "Career created successfully",
        "career": career_to_dict(career)
    }


@router.get("")
def get_careers(db: Session = Depends(get_db)):
    careers = db.query(Career).filter(Career.status == True).all()

    return {
        "careers": [career_to_dict(career) for career in careers]
    }


@router.get("/{career_id}")
def get_career(
    career_id: UUID,
    db: Session = Depends(get_db)
):
    career = db.query(Career).filter(Career.career_id == career_id).first()

    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    return career_to_dict(career)


@router.put("/{career_id}")
def update_career(
    career_id: UUID,
    career_data: CareerUpdate,
    db: Session = Depends(get_db)
):
    career = db.query(Career).filter(Career.career_id == career_id).first()

    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    update_data = career_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(career, key, value)

    db.commit()
    db.refresh(career)

    return {
        "message": "Career updated successfully",
        "career": career_to_dict(career)
    }


@router.delete("/{career_id}")
def delete_career(
    career_id: UUID,
    db: Session = Depends(get_db)
):
    career = db.query(Career).filter(Career.career_id == career_id).first()

    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    career.status = False
    db.commit()
    db.refresh(career)

    return {
        "message": "Career deleted successfully"
    }