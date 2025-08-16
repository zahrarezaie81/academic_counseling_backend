from sqlalchemy.orm import Session
from app.models import StudyPlan, StudyActivity, Counselor
from app.schemas import StudyPlanCreate, ActivityStatusUpdate, StudyActivityOut
from datetime import datetime
from fastapi import HTTPException
from app.utils.datetime import jalali_to_gregorian, to_jalali_str
from app import models
from sqlalchemy.orm import joinedload
from app.utils.datetime import to_jalali_str
from app.routers.notifications import manager


async def create_study_plan(db, counselor_user_id: int, data) -> StudyPlan:
    counselor = db.query(Counselor).filter(Counselor.user_id == counselor_user_id).first()
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")

    student = db.query(models.Student).filter(models.Student.student_id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    new_plan = StudyPlan(
        counselor_id=counselor.counselor_id,
        student_id=student.student_id,
        is_finalized=False
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    for act in data.activities:
        db.add(StudyActivity(
            plan_id=new_plan.plan_id,
            date=jalali_to_gregorian(act.date) if isinstance(act.date, str) else act.date,
            start_time=act.start_time,
            end_time=act.end_time,
            title=act.title,
            description=act.description
        ))
    db.commit()

    counselor_user = db.query(models.User).get(counselor.user_id)  
    student_user_id = student.user_id                       

    message = f"برنامه‌ی جدیدی توسط مشاور {counselor_user.firstname} {counselor_user.lastname} برای شما ایجاد شد."

    await manager.send_personal_message(message, student_user_id)
    db.add(models.Notification(user_id=student_user_id, message=message))
    db.commit()

    return new_plan


def finalize_plan(db: Session, plan_id: int):
    plan = db.query(StudyPlan).filter(StudyPlan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.is_finalized = True
    db.commit()


def get_student_weekly_plan(db: Session, student_user_id: int):
    student = db.query(models.Student).filter(models.Student.user_id == student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    plan = db.query(StudyPlan).options(joinedload(StudyPlan.activities)).filter(
        StudyPlan.student_id == student.student_id,
        StudyPlan.is_finalized == True
    ).order_by(StudyPlan.created_at.desc()).first()

    if not plan:
        return None

    activities_by_date = {}
    for a in plan.activities:
        jdate = to_jalali_str(a.date)
        if jdate not in activities_by_date:
            activities_by_date[jdate] = []

        activities_by_date[jdate].append(StudyActivityOut(
            activity_id=a.activity_id,
            date=jdate,
            start_time=a.start_time,
            end_time=a.end_time,
            title=a.title,
            description=a.description,
            status=a.status,
            student_note=a.student_note
        ))

    return {
        "plan_id": plan.plan_id,
        "score": plan.score if plan.score is not None else None,
        "feedback": plan.counselor_feedback if plan.counselor_feedback else None,
        "is_submitted_by_student": plan.is_submitted_by_student,
        "counselor_feedback": plan.counselor_feedback,
        "activities_by_date": activities_by_date
    }

def update_activity_status(db: Session, user_id: int, updates: list[ActivityStatusUpdate]):
    student = db.query(models.Student).filter(models.Student.user_id == user_id).first()
    if not student:
        raise HTTPException(404, detail="Student not found")
    
    student_id = student.student_id
    updated = False

    for upd in updates:
        activity = db.query(StudyActivity).join(StudyPlan).filter(
            StudyActivity.activity_id == upd.activity_id,
            StudyPlan.student_id == student_id,
            StudyActivity.plan_id == StudyPlan.plan_id
        ).first()
        if activity:
            activity.status = upd.status
            activity.student_note = upd.student_note
            updated = True

    if updated:
        db.commit()

def student_submit_status(db: Session, user_id: int):
    student = db.query(models.Student).filter(models.Student.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    plan = db.query(StudyPlan).filter(
        StudyPlan.student_id == student.student_id,
        StudyPlan.is_finalized == True
    ).order_by(StudyPlan.created_at.desc()).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No finalized plan found")

    plan.is_submitted_by_student = True
    plan.student_submit_time = datetime.utcnow()
    db.commit()


def submit_counselor_feedback(db: Session, plan_id: int, feedback_text: str):
    plan = db.query(StudyPlan).filter(StudyPlan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.counselor_feedback = feedback_text
    plan.counselor_feedback_time = datetime.utcnow()
    db.commit()



def get_plan_for_review(db: Session, student_id: int):

    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    user = db.query(models.User).filter(models.User.userid == student.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = db.query(StudyPlan).options(joinedload(StudyPlan.activities)).filter(
        StudyPlan.student_id == student_id,
        StudyPlan.is_submitted_by_student == True
    ).order_by(StudyPlan.student_submit_time.desc()).first()

    activities_by_date = {}

    if plan:
        for a in plan.activities:
            jdate = to_jalali_str(a.date)
            if jdate not in activities_by_date:
                activities_by_date[jdate] = []

            activities_by_date[jdate].append(StudyActivityOut(
                activity_id=a.activity_id,
                date=jdate,
                start_time=a.start_time,
                end_time=a.end_time,
                title=a.title,
                description=a.description,
                status=a.status,
                student_note=a.student_note
            ))

    return {
        "student_info": {
            "student_id": student.student_id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "phone_number": student.phone_number,
            "province": student.province,
            "city": student.city,
            "education_year": student.educational_level,
            "field_of_study": student.field_of_study,
            "semester_or_year": student.semester_or_year,
            "gpa": student.gpa,
            "profile_image_url": user.profile_image_url
        },
        "study_plan": {
            "plan_id": plan.plan_id if plan else None,
            "score": plan.score if plan else None,
            "is_submitted_by_student": plan.is_submitted_by_student if plan else None,
            "counselor_feedback": plan.counselor_feedback if plan else None,
            "activities_by_date": activities_by_date
        }
    }


def set_plan_score(db: Session, plan_id: int, score: int):
    plan = db.query(StudyPlan).filter(
        StudyPlan.plan_id == plan_id,
        StudyPlan.is_submitted_by_student == True
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or not submitted by student")

    plan.score = score
    db.commit()
    return {"detail": "Score saved"}


def create_recommendation(db: Session, student_id: int, counselor_id: int, suggested_course: str):
    recommendation = models.Recommendation(
        student_id=student_id,
        counselor_id=counselor_id,
        suggested_course=suggested_course
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation  
