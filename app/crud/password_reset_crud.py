from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import crud
from app.utils import otp
from app.utils.email import send_email
from app.schemas import SendCodeIn, ResetIn

def send_reset_code_service(data: SendCodeIn, db: Session) -> dict:
    user = crud.users_crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = otp.generate_code(data.email)
    send_email(
        to_email=data.email,
        subject="بازیابی رمز عبور",
        body=(
            f"کد بازیابی رمز عبور شما: {code}\n"
            f"این کد به مدت ۵ دقیقه معتبر است."
        )
    )
    return {"message": "Verification code sent to email"}

def verify_and_reset_service(data: ResetIn, db: Session) -> dict:
    if not otp.verify_code(data.email, data.code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    success = crud.users_crud.change_user_password(db, data.email, data.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Password reset failed")

    return {"message": "Password updated successfully"}
