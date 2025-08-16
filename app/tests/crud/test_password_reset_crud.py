import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.crud import password_reset_crud
from app.schemas import SendCodeIn, ResetIn


# ---------- send_reset_code_service ----------
def test_send_reset_code_service_success():
    mock_user = MagicMock()

    with patch.object(password_reset_crud.crud.users_crud, "get_user_by_email", return_value=mock_user) as mock_get_user, \
         patch.object(password_reset_crud.otp, "generate_code", return_value="123456") as mock_generate_code, \
         patch.object(password_reset_crud, "send_email") as mock_send_email:

        data = SendCodeIn(email="test@example.com")
        db = MagicMock()

        result = password_reset_crud.send_reset_code_service(data, db)

        assert result == {"message": "Verification code sent to email"}
        mock_get_user.assert_called_once_with(db, "test@example.com")
        mock_generate_code.assert_called_once_with("test@example.com")
        mock_send_email.assert_called_once()
        

def test_send_reset_code_service_user_not_found():
    with patch.object(password_reset_crud.crud.users_crud, "get_user_by_email", return_value=None):
        data = SendCodeIn(email="missing@example.com")
        db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            password_reset_crud.send_reset_code_service(data, db)

        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail


# ---------- verify_and_reset_service ----------
def test_verify_and_reset_service_success():
    with patch.object(password_reset_crud.otp, "verify_code", return_value=True) as mock_verify, \
         patch.object(password_reset_crud.crud.users_crud, "change_user_password", return_value=True) as mock_change_pw:

        data = ResetIn(email="test@example.com", code="123456", new_password="newpassword")
        db = MagicMock()

        result = password_reset_crud.verify_and_reset_service(data, db)

        assert result == {"message": "Password updated successfully"}
        mock_verify.assert_called_once_with("test@example.com", "123456")
        mock_change_pw.assert_called_once_with(db, "test@example.com", "newpassword")


def test_verify_and_reset_service_invalid_code():
    with patch.object(password_reset_crud.otp, "verify_code", return_value=False):
        data = ResetIn(email="test@example.com", code="bdcode", new_password="newpassword")
        db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            password_reset_crud.verify_and_reset_service(data, db)

        assert exc.value.status_code == 400
        assert "Invalid or expired code" in exc.value.detail


def test_verify_and_reset_service_password_change_failed():
    with patch.object(password_reset_crud.otp, "verify_code", return_value=True), \
         patch.object(password_reset_crud.crud.users_crud, "change_user_password", return_value=False):

        data = ResetIn(email="test@example.com", code="123456", new_password="newpassword")
        db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            password_reset_crud.verify_and_reset_service(data, db)

        assert exc.value.status_code == 500
        assert "Password reset failed" in exc.value.detail
