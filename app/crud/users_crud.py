from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app import models, schemas, auth
import os
from dotenv import load_dotenv
import boto3

load_dotenv()

LIARA_ENDPOINT = os.getenv("LIARA_ENDPOINT_URL")
LIARA_ACCESS_KEY = os.getenv("LIARA_ACCESS_KEY")
LIARA_SECRET_KEY = os.getenv("LIARA_SECRET_KEY")
LIARA_BUCKET_NAME = os.getenv("BUCKET_NAME")

s3 = boto3.client(
    "s3",
    endpoint_url=LIARA_ENDPOINT,
    aws_access_key_id=LIARA_ACCESS_KEY,
    aws_secret_access_key=LIARA_SECRET_KEY,
)

def upload_file_to_s3(file: UploadFile):
    s3.upload_fileobj(file.file, LIARA_BUCKET_NAME, file.filename)
    return file.filename

def update_user_profile_with_image(db: Session, user_id: int, file: UploadFile):
    user = db.query(models.User).filter(models.User.userid == user_id).first()
    file_name = upload_file_to_s3(file)
    profile_image_url = f"https://{LIARA_BUCKET_NAME}.storage.c2.liara.space/{file_name}"
    user.profile_image_filename = file_name
    user.profile_image_url = profile_image_url
    db.commit()
    db.refresh(user)
    return user

def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        return None

    db_user = models.User(
        firstname=user_in.firstname,
        lastname=user_in.lastname,
        email=user_in.email,
        password_hash=auth.get_hashed_password(user_in.password),
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    if user_in.role == models.RoleEnum.student:
        db.add(models.Student(user_id=db_user.userid))
    elif user_in.role == models.RoleEnum.counselor:
        db.add(models.Counselor(user_id=db_user.userid))

    db.commit()
    return db_user

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, userid: int) -> models.User | None:
    return db.query(models.User).get(userid)

def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = get_user_by_email(db, email)
    if not user or not auth.verify_password(password, user.password_hash):
        return None
    return user

def change_user_password(db: Session, email: str, new_password: str) -> bool:
    user = get_user_by_email(db, email)
    if not user:
        return False
    user.password_hash = auth.get_hashed_password(new_password)
    db.commit()
    db.refresh(user)
    return True

def update_user_password(db: Session, userid: int, new_password: str) -> models.User:
    user = get_user_by_id(db, userid)
    user.password_hash = auth.get_hashed_password(new_password)
    db.commit()
    db.refresh(user)
    return user

def update_user_role(db: Session, userid: int, new_role: str) -> models.User:
    user = get_user_by_id(db, userid)
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, userid: int) -> bool:
    user = get_user_by_id(db, userid)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

def update_user_profile(db: Session, user_id: int, user_in: schemas.StudentUpdate | schemas.CounselorUpdate):
    user = db.query(models.User).filter(models.User.userid == user_id).first()
    if user:
        if user_in.firstname:
            user.firstname = user_in.firstname
        if user_in.lastname:
            user.lastname = user_in.lastname
        if user_in.email:
            user.email = user_in.email
        db.commit()
        db.refresh(user)
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")