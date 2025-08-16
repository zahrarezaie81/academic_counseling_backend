from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Time, Date
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
import enum
from .database import Base

# Base = declarative_base()

# ----- ENUM DEFINITIONS -----

class RoleEnum(enum.Enum):
    student = "student"
    counselor = "counselor"
    admin = "admin"

class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    cancelled = "cancelled"

class NotificationStatus(str, enum.Enum):
    unread = "unread"
    read = "read"

class ActivityStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    not_done = "not_done"

# ----- USER -----

class User(Base):
    __tablename__ = "users"

    userid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(PGEnum(RoleEnum, name="role_enum"), nullable=False, default=RoleEnum.student)
    registrationDate = Column(DateTime, default=datetime.utcnow)
    profile_image_url = Column(String, nullable=True)
    profile_image_filename = Column(String, nullable=True)

    student = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    counselor = relationship("Counselor", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

# ----- STUDENT -----

class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    province = Column(String, nullable=True)
    city = Column(String, nullable=True)
    educational_level = Column(String, nullable=True)  
    field_of_study = Column(String, nullable=True)   
    semester_or_year = Column(String, nullable=True)   
    gpa = Column(Float, nullable=True)

    user = relationship("User", back_populates="student", passive_deletes=True)
    appointments = relationship("Appointment", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    recommendations = relationship("Recommendation", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    feedbacks = relationship("Feedback", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)
    study_plans = relationship("StudyPlan", back_populates="student", cascade="all, delete-orphan", passive_deletes=True)

# ----- COUNSELOR -----

class Counselor(Base):
    __tablename__ = "counselors"

    counselor_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    province = Column(String, nullable=True)
    city = Column(String, nullable=True)
    department = Column(String, nullable=True)

    user = relationship("User", back_populates="counselor", passive_deletes=True)
    time_ranges = relationship("CounselorTimeRange", back_populates="counselor", cascade="all, delete-orphan", passive_deletes=True)
    appointments = relationship("Appointment", back_populates="counselor", cascade="all, delete-orphan", passive_deletes=True)
    feedbacks = relationship("Feedback", back_populates="counselor", cascade="all, delete-orphan", passive_deletes=True)
    study_plans = relationship("StudyPlan", back_populates="counselor", cascade="all, delete-orphan", passive_deletes=True)
    recommendations = relationship("Recommendation", back_populates="counselor", cascade="all, delete-orphan", passive_deletes=True)

# ----- STUDY PLAN -----

class StudyPlan(Base):
    __tablename__ = "study_plans"

    plan_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    counselor_id = Column(Integer, ForeignKey("counselors.counselor_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_finalized = Column(Boolean, default=False)
    is_submitted_by_student = Column(Boolean, default=False)
    student_submit_time = Column(DateTime, nullable=True)
    counselor_feedback = Column(String, nullable=True)
    counselor_feedback_time = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="study_plans", passive_deletes=True)
    counselor = relationship("Counselor", back_populates="study_plans", passive_deletes=True)
    activities = relationship("StudyActivity", back_populates="plan", cascade="all, delete-orphan", passive_deletes=True)

# ----- STUDY ACTIVITY -----

class StudyActivity(Base):
    __tablename__ = "study_activities"

    activity_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("study_plans.plan_id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(PGEnum(ActivityStatus, name="activity_status_enum"), default=ActivityStatus.pending)
    student_note = Column(String, nullable=True)

    plan = relationship("StudyPlan", back_populates="activities", passive_deletes=True)

# ----- APPOINTMENT -----

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    counselor_id = Column(Integer, ForeignKey("counselors.counselor_id", ondelete="CASCADE"), nullable=False)
    slot_id = Column(Integer, ForeignKey("available_time_slots.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    status = Column(PGEnum(AppointmentStatus, name="appointment_status_enum"), default=AppointmentStatus.pending)
    notes = Column(String, nullable=True)

    student = relationship("Student", back_populates="appointments", passive_deletes=True)
    counselor = relationship("Counselor", back_populates="appointments", passive_deletes=True)
    slot = relationship("AvailableTimeSlot", passive_deletes=True)

# ----- COUNSELOR TIME RANGE -----

class CounselorTimeRange(Base):
    __tablename__ = "counselor_time_ranges"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    counselor_id = Column(Integer, ForeignKey("counselors.counselor_id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    from_time = Column(Time, nullable=False)
    to_time = Column(Time, nullable=False)
    duration = Column(Integer, nullable=False)

    counselor = relationship("Counselor", back_populates="time_ranges", passive_deletes=True)
    slots = relationship("AvailableTimeSlot", back_populates="time_range", cascade="all, delete-orphan", passive_deletes=True)

# ----- AVAILABLE TIME SLOT -----

class AvailableTimeSlot(Base):
    __tablename__ = "available_time_slots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    range_id = Column(Integer, ForeignKey("counselor_time_ranges.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_reserved = Column(Boolean, default=False)

    time_range = relationship("CounselorTimeRange", back_populates="slots", passive_deletes=True)

# ----- RECOMMENDATION -----

class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    counselor_id = Column(Integer, ForeignKey("counselors.counselor_id", ondelete="CASCADE"), nullable=False)
    suggested_course = Column(String, nullable=True)

    student = relationship("Student", back_populates="recommendations", passive_deletes=True)
    counselor = relationship("Counselor", back_populates="recommendations", passive_deletes=True)

# ----- FEEDBACK -----

class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    counselor_id = Column(Integer, ForeignKey("counselors.counselor_id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=True)
    comment = Column(String, nullable=True)
    date_submitted = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="feedbacks", passive_deletes=True)
    counselor = relationship("Counselor", back_populates="feedbacks", passive_deletes=True)

# ----- NOTIFICATION -----

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)
    message = Column(String, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications", passive_deletes=True)