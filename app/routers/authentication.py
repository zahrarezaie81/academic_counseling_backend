from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud, auth, models
from app.database import get_db
import os
import secrets
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(env_path))

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.create_user(db, user_in)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return user

@router.post("/login/", response_model=schemas.Token)
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):

    if (
        secrets.compare_digest(form_data.email, ADMIN_EMAIL) and
        secrets.compare_digest(form_data.password, ADMIN_PASSWORD)
    ):
        access_token = auth.create_access_token(subject="admin", role=models.RoleEnum.admin)
        refresh_token = auth.create_refresh_token(subject="admin")
        return {"access_token": access_token, "refresh_token": refresh_token}

    user = crud.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = auth.create_access_token(subject=user.userid, role=user.role)
    refresh_token = auth.create_refresh_token(subject=user.userid)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/update-password/")
def change_password(request: schemas.PasswordChangeRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = crud.change_user_password(db, request.email, request.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Password update failed")
    return {"message": "Password updated successfully"}

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(token: schemas.Token, db: Session = Depends(get_db)):
    payload = auth.decode_token(token.refresh_token, refresh=True)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    user_id = int(payload.get("sub"))
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_access = auth.create_access_token(subject=user.userid, role=user.role)
    new_refresh = auth.create_refresh_token(subject=user.userid)
    return {"access_token": new_access, "refresh_token": new_refresh}
