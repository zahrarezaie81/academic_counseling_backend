from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app import schemas
from app.auth import verify_admin
from app.database import get_db
from app import crud
from app.models import RoleEnum
from app.schemas import StudentGradeOut
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(role: Optional[RoleEnum] = None, db: Session = Depends(get_db)):
    return crud.list_users(db, role=role)

@router.post("/users", response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    return crud.create_user(db, user_in)

@router.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, user_in: schemas.UserUpdate, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    return crud.update_user(db, user_id, user_in)

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    crud.delete_user(db, user_id)
    return {"detail": "User deleted"}


@router.get("/counselors/{counselor_id}/students")
def list_students(counselor_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    return crud.get_students_by_counselor(db, counselor_id)

@router.get("/counselors/{counselor_id}/grades",  response_model=List[StudentGradeOut])
def student_grades(counselor_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    return crud.get_student_grades_by_counselor(db, counselor_id)

@router.get("/study-plans")
def all_study_plans(status: Optional[str] = None, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    return crud.get_study_plans(db, status)

@router.get("/appointments")
def all_appointments(status: Optional[str] = None, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    return crud.get_appointments(db, status)

@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    success = crud.delete_appointment_by_id(db, appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"detail": "Appointment deleted"}

@router.get("/dashboard", response_model=schemas.AdminDashboardOut)
def admin_dashboard(db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    return crud.get_admin_dashboard_data(db)