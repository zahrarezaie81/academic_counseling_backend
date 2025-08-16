from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app import crud, schemas, auth, models
from app.database import get_db
from app.auth import JWTBearer
router = APIRouter(
    prefix="/counselors",
    tags=["counselors"]
)

@router.get("/me/", response_model=schemas.CounselorOut)
def get_counselor_info(
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    return crud.get_counselor_info(db, payload)

@router.get("/{counselor_id}/", response_model=schemas.CounselorOut)
def get_counselor_by_id(
    counselor_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    return crud.get_counselor_by_id_service(db, counselor_id)

@router.get("/", response_model=list[schemas.CounselorsDisplay])
def get_counselors(db: Session = Depends(get_db)):
    counselors = crud.get_all_counselors(db)
    if not counselors:
        raise HTTPException(status_code=404, detail="No counselors found")
    return counselors
@router.put("/upload-profile/", response_model=schemas.UserOut)
def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    user_id = int(payload.get("sub"))
    return crud.update_user_profile_with_image(db, user_id, file)

@router.put("/update-profile/", response_model=schemas.CounselorUpdate)
def update_counselor(
    counselor_in: schemas.CounselorUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    return crud.update_counselor_profile_service(db, payload, counselor_in)


@router.get("/my-students")
def my_students(db: Session = Depends(get_db), payload: dict = Depends(JWTBearer())):
    user_id = payload["sub"]
    counselor = db.query(models.Counselor).filter(models.Counselor.user_id == user_id).first()
    if not counselor:
        return []
    return crud.get_students_of_counselor(db, counselor.counselor_id)

@router.get("/students/{student_id}", response_model=schemas.StudentDetails)
def get_student_info(student_id: int, db: Session = Depends(get_db)):
    data = crud.get_student_details(db, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="Student not found")
    return data

@router.get("/dashboard")
def get_counselor_dashboard(
    db: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    counselor_user_id = payload["sub"]
    return crud.get_counselor_dashboard_data(db, counselor_user_id)



