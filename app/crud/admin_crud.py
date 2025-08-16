from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models, schemas, crud
from app.crud import users_crud
from typing import Optional
from app.models import RoleEnum

def list_users(db: Session, role: Optional[RoleEnum] = None):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    return query.all()

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.userid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    student = db.query(models.Student).filter(models.Student.user_id == user_id).first()
    if student:
        db.delete(student)

    counselor = db.query(models.Counselor).filter(models.Counselor.user_id == user_id).first()
    if counselor:
        db.delete(counselor)

    db.delete(user)
    db.commit()


def update_user(db: Session, user_id: int, user_in: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.userid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.firstname:
        user.firstname = user_in.firstname
    if user_in.lastname:
        user.lastname = user_in.lastname
    if user_in.email:
        user.email = user_in.email

    db.commit()
    db.refresh(user)
    return user

def create_user(db: Session, user_in: schemas.UserCreate):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return users_crud.create_user(db, user_in)

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User, Student, Counselor, StudyPlan, Appointment, RoleEnum, AppointmentStatus

def get_students_by_counselor(db: Session, counselor_id: int):
    return (
        db.query(Student)
        .join(Appointment)
        .filter(Appointment.counselor_id == counselor_id and Appointment.status == AppointmentStatus.approved) 
        .all()
    )

def get_student_grades_by_counselor(db: Session, counselor_id: int):
    return (
        db.query(User.firstname, User.lastname, StudyPlan.score)
        .join(Student, Student.student_id == StudyPlan.student_id)
        .join(User, User.userid == Student.user_id)
        .filter(StudyPlan.counselor_id == counselor_id)
        .all()
    )


def get_study_plans(db: Session, status: str = None):
    query = db.query(StudyPlan)
    if status == "finalized":
        query = query.filter(StudyPlan.is_finalized.is_(True))
    elif status == "pending":
        query = query.filter(StudyPlan.is_finalized.is_(False))
    return query.all()

def get_appointments(db: Session, status: str = None):
    query = db.query(Appointment)
    if status:
        query = query.filter(Appointment.status == status)
    return query.all()

def delete_appointment_by_id(db: Session, appointment_id: int):
    obj = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if obj:
        db.delete(obj)
        db.commit()
        return True
    return False

def get_admin_dashboard_data(db: Session):
    active_users = db.query(User).filter(User.role != RoleEnum.admin).count()

    last_week = datetime.utcnow() - timedelta(days=7)
    done_appointments = db.query(Appointment).filter(
        Appointment.status == AppointmentStatus.approved,
        Appointment.date >= last_week.date()
    ).count()

    top_counselors = (
        db.query(
            User.firstname,
            User.lastname,
            func.count(Appointment.id).label("session_count")
        )
        .join(Counselor, Counselor.user_id == User.userid)
        .join(Appointment, Appointment.counselor_id == Counselor.counselor_id)
        .filter(Appointment.status == AppointmentStatus.approved)
        .group_by(User.userid)
        .order_by(func.count(Appointment.id).desc())
        .limit(5)
        .all()
    )
    result = {
        "active_users": active_users,
        "done_appointments_last_week": done_appointments,
        "top_counselors": [
            {
                "firstname": fname,
                "lastname": lname,
                "session_count": count
            }
            for fname, lname, count in top_counselors
        ]
    }

    return result
