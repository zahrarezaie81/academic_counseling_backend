from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, auth, models
from app.database import get_db
from typing import List
from app.auth import JWTBearer

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"]
)

@router.post("/book/", response_model=schemas.AppointmentOut)
async def book_appointment(
    data: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    user_id = int(payload.get("sub"))
    student = db.query(models.Student).filter(models.Student.user_id == user_id).first()
    student_user = crud.get_user_by_id(db, user_id)

    if student_user.role != models.RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can book appointments.")

    return await crud.create_appointment(
        db,
        student_id=student.student_id,
        slot_id=data.slot_id,
        notes=data.notes
    )

@router.post("/{appointment_id}/approve", response_model=schemas.AppointmentOut)
async def approve_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    user_id = int(payload.get("sub"))
    user = crud.get_user_by_id(db, user_id)
    if user.role != models.RoleEnum.counselor:
        raise HTTPException(403, "Only counselors can approve appointments")

    return await crud.approve_appointment(db, appointment_id)


@router.delete("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    return crud.cancel_appointment(db, appointment_id)



@router.get("/pending", response_model=List[schemas.AppointmentItem])
def get_pending_appointments(
    db: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    counselor_user_id = payload["sub"]
    return crud.get_appointments_by_status(db, counselor_user_id, schemas.AppointmentStatus.pending)


@router.get("/approved", response_model=List[schemas.AppointmentItem])
def get_approved_appointments(
    db: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    counselor_user_id = payload["sub"]
    return crud.get_appointments_by_status(db, counselor_user_id, schemas.AppointmentStatus.approved)
