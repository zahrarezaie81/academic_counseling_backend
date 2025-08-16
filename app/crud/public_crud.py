from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models, schemas
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.utils.datetime import to_jalali_str


def get_all_counselors(db: Session):
    return (
        db.query(
            models.Counselor.counselor_id,
            models.User.firstname,
            models.User.lastname,
            models.User.profile_image_url
        )
        .join(models.Counselor, models.User.userid == models.Counselor.user_id)
        .filter(models.User.role == schemas.RoleEnum.counselor)
        .all()
    ) 
    
def leave_feedback(db: Session, student_user_id: int, counselor_id: int, rating: int = None, comment: str = None):
    student = db.query(models.Student).filter(models.Student.user_id == student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    has_appointment = db.query(models.Appointment).filter(
        models.Appointment.student_id == student.student_id,
        models.Appointment.counselor_id == counselor_id,
        models.Appointment.status == models.AppointmentStatus.approved
    ).first()

    if not has_appointment:
        raise HTTPException(status_code=403, detail="You can only leave feedback after an approved appointment.")

    feedback = models.Feedback(
        student_id=student.student_id,
        counselor_id=counselor_id,
        rating=rating,
        comment=comment
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_public_counselor_info(db: Session, counselor_id: int):
    counselor = db.query(models.Counselor).options(joinedload(models.Counselor.user)).filter(
        models.Counselor.counselor_id == counselor_id
    ).first()

    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")

    raw_slots = db.query(
        models.AvailableTimeSlot.id,
        models.AvailableTimeSlot.start_time,
        models.AvailableTimeSlot.end_time,
        models.AvailableTimeSlot.is_reserved,
        models.CounselorTimeRange.date
    ).join(
        models.CounselorTimeRange,
        models.AvailableTimeSlot.range_id == models.CounselorTimeRange.id
    ).filter(
        models.CounselorTimeRange.counselor_id == counselor.counselor_id,
        models.AvailableTimeSlot.is_reserved == False
    ).all()

    free_slots = [
        {
            "id": s.id,
            "start_time": s.start_time.strftime("%H:%M:%S"),
            "end_time": s.end_time.strftime("%H:%M:%S"),
            "date": to_jalali_str(s.date),
            "is_reserved": s.is_reserved
        }
        for s in raw_slots
    ]

    feedbacks = db.query(models.Feedback).filter(
        models.Feedback.counselor_id == counselor.counselor_id
    ).all()

    return {
        "counselor_id": counselor.counselor_id,
        "firstname": counselor.user.firstname,
        "lastname": counselor.user.lastname,
        "email": counselor.user.email,
        "profile_image_url": counselor.user.profile_image_url,
        "phone_number": counselor.phone_number,
        "province": counselor.province,
        "city": counselor.city,
        "department": counselor.department,
        "feedbacks": feedbacks,
        "free_slots": free_slots
    }
