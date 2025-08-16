from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.database import get_db
from app.auth import JWTBearer

router = APIRouter(
    prefix="/public",
    tags=["public"]
)

@router.get("/counselors/", response_model=list[schemas.CounselorsDisplay])
def get_all_counselors(db: Session = Depends(get_db)):
    counselors = crud.get_all_counselors(db)
    if not counselors:
        raise HTTPException(status_code=404, detail="No counselors found")
    return counselors


@router.post("/counselors/{counselor_id}/comment")
def leave_feedback_route(
    counselor_id: int,
    data: schemas.FeedbackCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    student_user_id = payload["sub"]
    return crud.leave_feedback(
        db=db,
        student_user_id=student_user_id,
        counselor_id=counselor_id,
        rating=data.rating,
        comment=data.comment
    )


@router.get("/counselor/{counselor_id}", response_model=schemas.PublicCounselorOut)
def get_counselor_public(counselor_id: int, db: Session = Depends(get_db)):
    return crud.get_public_counselor_info(db, counselor_id)
