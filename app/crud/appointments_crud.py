from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models
from datetime import datetime
from typing import Optional
from app.utils.datetime import to_jalali_str
from app.models import Appointment, Notification
from app.routers.notifications import manager
import asyncio

async def create_appointment(db: Session, student_id: int, slot_id: int, notes: Optional[str] = None):
    slot = db.query(models.AvailableTimeSlot).filter(models.AvailableTimeSlot.id == slot_id).first()
    if not slot or slot.is_reserved:
        raise HTTPException(400, "Slot not available")
    range = db.query(models.CounselorTimeRange).filter(models.CounselorTimeRange.id == slot.range_id).first()
    counselor_id = slot.time_range.counselor_id
    appointment = models.Appointment(
        student_id=student_id,
        counselor_id=counselor_id,
        slot_id=slot.id,
        date=slot.time_range.date,
        time=slot.start_time,
        status=models.AppointmentStatus.pending,
        notes=notes
    )
    slot = db.query(models.AvailableTimeSlot).filter(models.AvailableTimeSlot.id == appointment.slot_id).first()
    slot.is_reserved = True
    
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    student_user = db.query(models.User).filter(models.User.userid == student.user_id).first()
    counselor = db.query(models.Counselor).filter(models.Counselor.counselor_id == counselor_id).first()
    user_id = counselor.user_id
    jalali_date = to_jalali_str(range.date)
    message = f"دانش‌آموز {student_user.firstname} {student_user.lastname} یک جلسه برای تاریخ {jalali_date} ساعت {slot.end_time} رزرو کرده است."
    
    await manager.send_personal_message(message, user_id)
    
    db_notification = Notification(user_id=user_id, message=message)
    db.add(db_notification)
    db.commit()
    
    return appointment

async def approve_appointment(db: Session, appointment_id: int):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(404, "Appointment not found")

    appointment.status = models.AppointmentStatus.approved

    db.commit()
    db.refresh(appointment)

    student = db.query(models.Student).filter_by(student_id=appointment.student_id).first()
    counselor = db.query(models.Counselor).filter_by(counselor_id=appointment.counselor_id).first()

    student_user = student.user
    counselor_user = counselor.user

    user_id = student.user_id

    message = (
        f"جلسه شما با مشاور {counselor_user.firstname} {counselor_user.lastname} "
        f"برای تاریخ {appointment.date} ساعت {appointment.time} تایید شد."
    )
    asyncio.create_task(manager.send_personal_message(message, user_id))

    db_notification = models.Notification(user_id=user_id, message=message)
    db.add(db_notification)
    db.commit()

    return appointment

def cancel_appointment(db: Session, appointment_id: int):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    appointment.slot.is_reserved = False
    db.delete(appointment)
    db.commit()
    return True




def get_appointments_by_status(db: Session, counselor_user_id: int, status: models.AppointmentStatus):
    
    counselor = db.query(models.Counselor).filter(models.Counselor.user_id == counselor_user_id).first()
    if not counselor:
        return []

    appointments = db.query(models.Appointment, models.Student, models.User).join(models.Student, models.Appointment.student_id == models.Student.student_id) \
        .join(models.User, models.Student.user_id == models.User.userid) \
        .filter(
            models.Appointment.counselor_id == counselor.counselor_id,
            models.Appointment.status == status
        ).all()

    result = []
    for app, student, user in appointments:
        result.append({
            "appointment_id": app.id,
            "student_id": app.student_id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "date": to_jalali_str(app.date),
            "start_time": app.time,
            "end_time": app.slot.end_time 
        })
        print(app.status)
    return result
