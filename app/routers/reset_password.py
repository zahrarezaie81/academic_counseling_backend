from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ResetIn, SendCodeIn
from app.crud import password_reset_crud  

router = APIRouter(
    prefix="/password-reset",
    tags=["password-reset"]
)

@router.post("/send-code", status_code=200)
def send_reset_code(data: SendCodeIn, db: Session = Depends(get_db)):
    return password_reset_crud.send_reset_code_service(data, db)

@router.post("/verify-and-reset", status_code=200)
def verify_and_reset(data: ResetIn, db: Session = Depends(get_db)):
    return password_reset_crud.verify_and_reset_service(data, db)
