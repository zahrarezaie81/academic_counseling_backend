from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models, schemas, crud
from datetime import datetime, timedelta

def get_student_by_user_id(db: Session, user_id: int) -> models.Student | None:
    return db.query(models.Student).filter(models.Student.user_id == user_id).first()

def get_student_by_id(db: Session, student_id: int) -> models.Student | None:
    return db.query(models.Student).filter(models.Student.student_id == student_id).first()

def get_student_info(db: Session, payload: dict) -> schemas.StudentOut:
    user_id = int(payload.get("sub"))
    user = crud.get_user_by_id(db, user_id)
    student = get_student_by_user_id(db, user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return schemas.StudentOut(
        firstname=user.firstname,
        lastname=user.lastname,
        student_id=student.student_id,
        email=user.email,
        phone_number=student.phone_number,
        province=student.province,
        city=student.city,
        education_year=student.educational_level,
        field_of_study=student.field_of_study,
        semester_or_year=student.semester_or_year,
        gpa=student.gpa,
        profile_image_url=user.profile_image_url
    )

def update_student_profile(db: Session, student_id: int, student_in: schemas.StudentUpdate):
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if student:
        if student_in.phone_number:
            student.phone_number = student_in.phone_number
        if student_in.province:
            student.province = student_in.province
        if student_in.city:
            student.city = student_in.city
        if student_in.education_year:
            student.educational_level = student_in.education_year
        if student_in.field_of_study:
            student.field_of_study = student_in.field_of_study
        if student_in.semester_or_year:
            student.semester_or_year = student_in.semester_or_year    
        if student_in.gpa is not None:
            student.gpa = student_in.gpa
        db.commit()
        db.refresh(student)
        return student
    else:
        raise HTTPException(status_code=404, detail="Student not found")

def is_admin(role: schemas.RoleEnum) -> bool:
    return role == schemas.RoleEnum.admin

def is_own_data(user_id: int, data_id: int) -> bool:
    return user_id == data_id

def update_student_profile_service(db: Session, payload: dict, student_in: schemas.StudentUpdate) -> schemas.StudentUpdate:
    user_id = int(payload.get("sub"))
    user = crud.get_user_by_id(db, user_id)
    student = get_student_by_user_id(db, user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if is_admin(user.role) or is_own_data(user_id, student.user_id):
        student = update_student_profile(db, student.student_id, student_in)
        user = crud.update_user_profile(db, user_id, student_in)
        return schemas.StudentUpdate(
            student_id=student.student_id,
            firstname=user.firstname,
            lastname=user.lastname,
            email=user.email,
            phone_number=student.phone_number,
            province=student.province,
            city=student.city,
            education_year=student.educational_level,
            field_of_study=student.field_of_study,
            semester_or_year=student.semester_or_year,
            gpa=student.gpa
        )
    else:
        raise HTTPException(status_code=403, detail="Permission denied")

def delete_student(db: Session, student_id: int) -> bool:
    student = get_student_by_id(db, student_id)
    if student:
        db.delete(student)
        db.commit()
        return True
    return False


def get_progress_percentage(db: Session, student_id: int) -> float:

    plan = db.query(models.StudyPlan).filter(
        models.StudyPlan.student_id == student_id,
        models.StudyPlan.is_finalized == True,
        models.StudyPlan.is_submitted_by_student == True
    ).order_by(models.StudyPlan.student_submit_time.desc()).first()

    if not plan:
        return 0.0 

    total_activities = len(plan.activities)
    if total_activities == 0:
        return 0.0

    done_count = sum(1 for a in plan.activities if a.status == "done")
    return round((done_count / total_activities) * 100, 2)

def get_recommendations_for_student(db: Session, student_id: int):
    return db.query(models.Recommendation).filter(models.Recommendation.student_id == student_id).all()


def get_user_by_student_id(db: Session, student_id: int):
    student = db.query(models.Student).filter_by(student_id=student_id).first()
    if student:
        return db.query(models.User).filter_by(userid=student.user_id).first()
    return None