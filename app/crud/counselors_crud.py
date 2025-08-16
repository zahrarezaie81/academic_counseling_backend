from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models, schemas
from .users_crud import get_user_by_id, update_user_profile
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from datetime import datetime, timedelta, date
from sqlalchemy.orm import joinedload, Session
from sqlalchemy import func



def get_counselor_by_user_id(db: Session, user_id: int) -> models.Counselor | None:
    return db.query(models.Counselor).filter(models.Counselor.user_id == user_id).first()

def get_counselor_by_id(db: Session, counselor_id: int) -> models.Counselor | None:
    return db.query(models.Counselor).filter(models.Counselor.counselor_id == counselor_id).first()

def get_counselor_by_id_service(db: Session, counselor_id: int) -> schemas.CounselorOut:
    counselor = get_counselor_by_id(db, counselor_id)
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")
    user = get_user_by_id(db, counselor.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User associated with counselor not found")

    return schemas.CounselorOut(
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        phone_number=counselor.phone_number,
        province=counselor.province,
        city=counselor.city,
        department=counselor.department if counselor.department else None,
        profile_image_url=user.profile_image_url
    )

def get_counselor_info(db: Session, payload: dict) -> schemas.CounselorOut:
    user_id = int(payload.get("sub"))
    user = get_user_by_id(db, user_id)
    counselor = get_counselor_by_user_id(db, user_id)
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")

    return schemas.CounselorOut(
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        phone_number=counselor.phone_number,
        province=counselor.province,
        city=counselor.city,
        department=counselor.department if counselor.department else None,
        profile_image_url=user.profile_image_url
    )

def is_admin(role: schemas.RoleEnum) -> bool:
    return role == schemas.RoleEnum.admin

def is_own_data(user_id: int, data_id: int) -> bool:
    return user_id == data_id

def update_counselor_profile(db: Session, user_id: int, counselor_in: schemas.CounselorUpdate):
    counselor = db.query(models.Counselor).filter(models.Counselor.user_id == user_id).first()
    if counselor:
        if counselor_in.phone_number:
            counselor.phone_number = counselor_in.phone_number
        if counselor_in.province:
            counselor.province = counselor_in.province
        if counselor_in.city:
            counselor.city = counselor_in.city
        if counselor_in.department:
            counselor.department = counselor_in.department
        db.commit()
        db.refresh(counselor)
        return counselor
    return None

def update_counselor_profile_service(db: Session, payload: dict, counselor_in: schemas.CounselorUpdate) -> schemas.CounselorUpdate:
    user_id = int(payload.get("sub"))
    user = get_user_by_id(db, user_id)
    counselor = get_counselor_by_user_id(db, user_id)
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")

    if is_admin(user.role) or is_own_data(user_id, counselor.user_id):
        counselor = update_counselor_profile(db, counselor.user_id, counselor_in)
        user = update_user_profile(db, user_id, counselor_in)
        return schemas.CounselorUpdate(
            firstname=user.firstname,
            lastname=user.lastname,
            email=user.email,
            phone_number=counselor.phone_number,
            province=counselor.province,
            city=counselor.city,
            department=counselor.department if counselor.department else None
        )
    else:
        raise HTTPException(status_code=403, detail="Permission denied")

def delete_counselor(db: Session, counselor_id: int) -> bool:
    counselor = get_counselor_by_id(db, counselor_id)
    if counselor:
        db.delete(counselor)
        db.commit()
        return True
    return False


def get_students_of_counselor(
    db: Session,
    counselor_id: int,
    days_since_approved: int = 30,
    days_since_plan: int = 30,
):
  
    counselor = (
        db.query(models.Counselor)
        .filter(models.Counselor.counselor_id == counselor_id)
        .first()
    )
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")

    today = date.today()
    appt_cutoff = today - timedelta(days=days_since_approved)
    plan_cutoff_dt = datetime.utcnow() - timedelta(days=days_since_plan)
    last_approved_subq = (
        db.query(
            models.Appointment.student_id.label("student_id"),
            func.max(models.Appointment.date).label("last_date"),
        )
        .filter(
            models.Appointment.counselor_id == counselor.counselor_id,
            models.Appointment.status == models.AppointmentStatus.approved,
        )
        .group_by(models.Appointment.student_id)
        .subquery()
    )

    recent_by_appt_ids = {
        row.student_id
        for row in db.query(last_approved_subq.c.student_id)
        .filter(last_approved_subq.c.last_date >= appt_cutoff)
        .all()
    }

    open_plan_ids = {
        sid
        for (sid,) in db.query(models.StudyPlan.student_id)
        .filter(
            models.StudyPlan.counselor_id == counselor.counselor_id,
            models.StudyPlan.is_finalized == False,  
        )
        .distinct()
        .all()
    }
    recent_plan_ids = {
        sid
        for (sid,) in db.query(models.StudyPlan.student_id)
        .filter(
            models.StudyPlan.counselor_id == counselor.counselor_id,
            models.StudyPlan.created_at >= plan_cutoff_dt,
        )
        .distinct()
        .all()
    }

    eligible_student_ids = recent_by_appt_ids | open_plan_ids | recent_plan_ids
    if not eligible_student_ids:
        return []
    students = (
        db.query(models.Student)
        .options(joinedload(models.Student.user))
        .filter(models.Student.student_id.in_(eligible_student_ids))
        .all()
    )

    out: list[schemas.StudentOut] = []
    for s in students:
        u = s.user
        out.append(
            schemas.StudentOut(
                student_id=s.student_id,
                phone_number=s.phone_number,
                province=s.province,
                city=s.city,
                education_year=s.educational_level,
                field_of_study=s.field_of_study,
                semester_or_year=s.semester_or_year,
                gpa=s.gpa,
                profile_image_url=u.profile_image_url if u else None,
                firstname=u.firstname if u else "",
                lastname=u.lastname if u else "",
                email=u.email if u else "",
            )
        )
    return out

def get_counselor_dashboard_data(db: Session, counselor_user_id: int):

    counselor = db.query(models.Counselor).filter(models.Counselor.user_id == counselor_user_id).first()
    if not counselor:
        return {"error": "Counselor not found"}

    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)

    past_sessions = db.query(models.Appointment).filter(
        models.Appointment.counselor_id == counselor.counselor_id,
        models.Appointment.status == "approved",
        models.Appointment.date >= month_ago.date(),
        models.Appointment.date <= now.date()
    ).count()

    future_approved = db.query(models.Appointment).filter(
        models.Appointment.counselor_id == counselor.counselor_id,
        models.Appointment.status == "approved",
        models.Appointment.date > now.date()
    ).count()


    student_count = db.query(models.Appointment.student_id).filter(
        models.Appointment.counselor_id == counselor.counselor_id
    ).distinct().count()

    return {
        "recent_sessions": past_sessions,
        "upcoming_approved_requests": future_approved,
        "unique_students": student_count
    }

def get_student_details(db: Session, student_id: int):
    student = (
        db.query(models.Student, models.User)
        .join(models.User, models.Student.user_id == models.User.userid)
        .filter(models.Student.student_id == student_id)
        .first()
    )

    if not student:
        return None

    student_data, user_data = student
    return {
        "student_id": student_data.student_id,
        "firstname": user_data.firstname,
        "lastname": user_data.lastname,
        "email": user_data.email,
        "phone_number": student_data.phone_number,
        "province": student_data.province,
        "city": student_data.city,
        "education_year": student_data.educational_level,
        "field_of_study": student_data.field_of_study,
        "semester_or_year": student_data.semester_or_year,
        "gpa": student_data.gpa,
        "profile_image_url": user_data.profile_image_url,
    }
