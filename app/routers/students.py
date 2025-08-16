from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app import  schemas, auth, crud, models
from app.database import get_db
from app.auth import JWTBearer
from typing import List


router = APIRouter(
    prefix="/students",
    tags=["students"]
)

@router.get("/me/", response_model=schemas.StudentOut)
def get_student_info(
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    return crud.get_student_info(db, payload)

@router.put("/update-profile/", response_model=schemas.StudentUpdate)
def update_student(
    student_in: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    return crud.update_student_profile_service(db, payload, student_in)

@router.put("/upload-profile/", response_model=schemas.UserOut)
def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    user_id = int(payload.get("sub"))
    return crud.update_user_profile_with_image(db, user_id, file)

@router.get("/student/progress")
def get_progress(payload: dict = Depends(JWTBearer()), db: Session = Depends(get_db)):
    student_user_id = payload["sub"]
    student = db.query(models.Student).filter(models.Student.user_id == student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    percent = crud.get_progress_percentage(db, student.student_id)
    return {"progress_percent": percent}

@router.get("/my-recommendations", response_model=List[schemas.RecommendationOut])
def get_my_recommendations(
    db: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    student_user_id = payload["sub"]
    student = db.query(models.Student).filter(models.Student.user_id == student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return crud.get_recommendations_for_student(db, student.student_id)
