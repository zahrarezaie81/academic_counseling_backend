import re
from pydantic import  EmailStr, constr, BaseModel, validator, Field, conint
from .models import RoleEnum, AppointmentStatus
from app.utils.datetime import jalali_to_gregorian
from datetime import date, time, datetime
from typing import List, Optional, Literal


class PasswordChangeRequest(BaseModel):
    email: EmailStr
    new_password: constr(min_length=8)
    confirm_password: constr(min_length=8)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: str
    role: RoleEnum

    @validator('password')
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v  

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str

class UserOut(BaseModel):
    userid: int
    firstname: str
    lastname: str
    email: EmailStr
    role: RoleEnum
    profile_image_url: Optional[str] = None  
    profile_image_filename: Optional[str] = None  
    registrationDate: datetime

    class Config:
        from_attributes = True


class StudentOut(BaseModel):
    firstname: str
    lastname: str
    student_id: int
    email: str
    phone_number: Optional[str]
    province: Optional[str]
    city: Optional[str]
    education_year: Optional[str] 
    field_of_study: Optional[str] = Field(None, alias='field_of_study')
    semester_or_year: Optional[str] = None
    gpa: Optional[float]
    profile_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class CounselorOut(BaseModel):
    firstname: str
    lastname: str
    email: str
    phone_number: Optional[str]
    province: Optional[str]
    city: Optional[str]
    department: Optional[str]
    profile_image_url: Optional[str] = None
    class Config:
        from_attributes = True

        
class UserUpdate(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]
    email: Optional[EmailStr]
    class Config:
        from_attributes = True

class StudentUpdate(BaseModel):
    firstname: Optional[str] 
    lastname: Optional[str]  
    email: Optional[EmailStr] 
    phone_number: Optional[str] 
    province: Optional[str]
    city: Optional[str] 
    education_year: Optional[str] 
    field_of_study: Optional[str] = Field(None, alias='field_of_study')
    semester_or_year: Optional[str] = None
    gpa: Optional[float]
    
    
class CounselorUpdate(UserUpdate):
    phone_number: Optional[str]
    province: Optional[str]
    city: Optional[str]
    department: Optional[str]
    
    class Config:
        from_attributes = True
        
        
class CounselorsDisplay(BaseModel):
    counselor_id : int
    firstname: str
    lastname: str
    profile_image_url: Optional[str] = None
    class Config:
        from_attributes = True        
        



class TimeRangeInput(BaseModel):
    date: date
    from_time: time
    to_time: time
    duration_minutes: int

    @validator("date", pre=True)
    def convert_jalali(cls, v):
        if isinstance(v, str):
            return jalali_to_gregorian(v)
        return v


class TimeRangeOut(BaseModel):
    id: int
    counselor_id: int
    date: date
    from_time: time
    to_time: time
    duration: int

    class Config:
        from_attributes = True


class SlotOut(BaseModel):
    id: int
    start_time: time
    end_time: time
    is_reserved: bool

    class Config:
        from_attributes = True


class TimeRangeWithSlots(BaseModel):
    id: int
    date: date
    from_time: time
    to_time: time
    duration: int
    slots: List[SlotOut]

    class Config:
        from_attributes = True



class AppointmentCreate(BaseModel):
    slot_id: int
    notes: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    student_id: int
    counselor_id: int
    slot_id: int
    date: date
    time: time   
    status: AppointmentStatus
    notes: Optional[str] = None

    class Config:
        from_attributes = True
        


class AppointmentItem(BaseModel):
    appointment_id: int
    student_id : int
    firstname: str
    lastname: str
    date: str
    start_time: time
    end_time: time

    class Config:
        from_attributes = True

            
class SendCodeIn(BaseModel):
    email: EmailStr

class ResetIn(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6)
    new_password: constr(min_length=8)
        

class ActivityInput(BaseModel):
    date: str
    start_time: time
    end_time: time
    title: str
    description: Optional[str] = None

class StudyPlanCreate(BaseModel):
    student_id: int
    activities: List[ActivityInput]

class ActivityStatusUpdate(BaseModel):
    activity_id: int
    status: Literal["pending", "done", "not_done"]
    student_note: Optional[str] = None

class StudentStatusSubmit(BaseModel):
    activities: List[ActivityStatusUpdate]

class CounselorFeedback(BaseModel):
    plan_id: int
    feedback: str


class StudyActivityOut(BaseModel):
    activity_id: int
    date: str
    start_time: time
    end_time: time
    title: str
    description: Optional[str]
    status: str
    student_note: Optional[str]

    class Config:
        from_attribute = True

class StudyPlanOut(BaseModel):
    plan_id: int
    student_id: int
    counselor_id: int
    created_at: datetime
    is_finalized: bool
    is_submitted_by_student: bool
    counselor_feedback: Optional[str]
    activities: List[StudyActivityOut]

    class Config:
        from_attribute = True
        
class ScoreInput(BaseModel):
    plan_id: int
    score: conint(ge=0, le=100)        
      
class FeedbackCreate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None
      

class FeedbackOut(BaseModel):
    comment: Optional[str]
    rating: Optional[int]
    date_submitted: datetime

    class Config:
        from_attributes = True


class FreeSlotOut(BaseModel):
    id: int
    start_time: time
    end_time: time
    time_range_id: int

    class Config:
        from_attributes = True


class UserMiniOut(BaseModel):
    firstname: str
    lastname: str
    email: str
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True

class SlotWithDate(BaseModel):
    id: int
    start_time: time
    end_time: time
    date: str
    is_reserved: bool

    class Config:
        from_attributes = True
        
class PublicCounselorOut(BaseModel):
    counselor_id: int
    firstname: str
    lastname: str
    email: str
    profile_image_url: Optional[str]
    phone_number: Optional[str]
    province: Optional[str]
    city: Optional[str]
    department: Optional[str]
    feedbacks: List[FeedbackOut]
    free_slots: List[SlotWithDate]

    class Config:
        from_attributes = True


class FeedbackOut(BaseModel):
    comment: Optional[str]
    rating: Optional[int]
    date_submitted: datetime




class RecommendationCreate(BaseModel):
    student_id: int
    suggested_course: str

class RecommendationOut(BaseModel):
    recommendation_id: int
    suggested_course: str
    student_id: int

    
class NotificationCreate(BaseModel):
    user_id: int
    message: str

class NotificationOut(NotificationCreate):
    id: int
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True      

class Message(BaseModel):
    detail: str
    

class UserOut(BaseModel):
    userid: int
    firstname: str
    lastname: str
    email: str
    role: RoleEnum

    class Config:
        from_attributes = True
    

class TokenData(BaseModel):
    sub: str
    role: str 
    
    
class StudentGradeOut(BaseModel):
    firstname: str
    lastname: str
    score: Optional[int]
class TopCounselor(BaseModel):
    firstname: str
    lastname: str
    session_count: int

class AdminDashboardOut(BaseModel):
    active_users: int
    done_appointments_last_week: int
    top_counselors: List[TopCounselor]    
    
class StudentDetails(BaseModel):
    student_id: int
    firstname: str
    lastname: str
    email: str
    phone_number: Optional[str]
    province: Optional[str]
    city: Optional[str]
    education_year: Optional[str]
    field_of_study: Optional[str]
    semester_or_year: Optional[str]
    gpa: Optional[float]
    profile_image_url: Optional[str]
    
    