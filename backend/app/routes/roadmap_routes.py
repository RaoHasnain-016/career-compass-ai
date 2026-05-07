from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.career_model import Career
from app.models.roadmap_model import RoadmapStage
from app.schemas.roadmap_schema import RoadmapStageCreate, RoadmapStageUpdate

router = APIRouter(
    prefix="/roadmaps",
    tags=["Roadmaps"]
)


def roadmap_to_dict(stage: RoadmapStage):
    return {
        "stage_id": str(stage.stage_id),
        "career_id": str(stage.career_id),
        "stage_order": stage.stage_order,
        "title": stage.title,
        "description": stage.description,
        "required_skills": stage.required_skills or [],
        "suggested_resources": stage.suggested_resources or [],
        "status": stage.status,
    }


@router.post("")
def create_roadmap_stage(
    stage_data: RoadmapStageCreate,
    db: Session = Depends(get_db)
):
    career = db.query(Career).filter(
        Career.career_id == UUID(stage_data.career_id)
    ).first()

    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    stage = RoadmapStage(
        career_id=career.career_id,
        stage_order=stage_data.stage_order,
        title=stage_data.title,
        description=stage_data.description,
        required_skills=stage_data.required_skills,
        suggested_resources=stage_data.suggested_resources,
        status=stage_data.status,
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)

    return {
        "message": "Roadmap stage created successfully",
        "stage": roadmap_to_dict(stage)
    }


@router.get("/{career_id}")
def get_roadmap_by_career(
    career_id: UUID,
    db: Session = Depends(get_db)
):
    career = db.query(Career).filter(Career.career_id == career_id).first()

    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    stages = (
        db.query(RoadmapStage)
        .filter(
            RoadmapStage.career_id == career_id,
            RoadmapStage.status == True
        )
        .order_by(RoadmapStage.stage_order.asc())
        .all()
    )

    return {
        "career": {
            "career_id": str(career.career_id),
            "title": career.title,
            "field": career.field,
        },
        "roadmap": [roadmap_to_dict(stage) for stage in stages]
    }


@router.put("/{stage_id}")
def update_roadmap_stage(
    stage_id: UUID,
    stage_data: RoadmapStageUpdate,
    db: Session = Depends(get_db)
):
    stage = db.query(RoadmapStage).filter(
        RoadmapStage.stage_id == stage_id
    ).first()

    if not stage:
        raise HTTPException(status_code=404, detail="Roadmap stage not found")

    update_data = stage_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(stage, key, value)

    db.commit()
    db.refresh(stage)

    return {
        "message": "Roadmap stage updated successfully",
        "stage": roadmap_to_dict(stage)
    }


@router.delete("/{stage_id}")
def delete_roadmap_stage(
    stage_id: UUID,
    db: Session = Depends(get_db)
):
    stage = db.query(RoadmapStage).filter(
        RoadmapStage.stage_id == stage_id
    ).first()

    if not stage:
        raise HTTPException(status_code=404, detail="Roadmap stage not found")

    stage.status = False
    db.commit()
    db.refresh(stage)

    return {
        "message": "Roadmap stage deleted successfully"
    }