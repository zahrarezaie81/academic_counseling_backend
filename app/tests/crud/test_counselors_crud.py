import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from datetime import date
from app import schemas
from app.crud import counselors_crud


class DummyUser:
    def __init__(self, userid=1, firstname="John", lastname="Doe", email="john@example.com", role=schemas.RoleEnum.admin, profile_image_url="img.jpg"):
        self.userid = userid
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.role = role
        self.profile_image_url = profile_image_url


class DummyCounselor:
    def __init__(self, counselor_id=1, user_id=1, phone_number="12345", province="Province", city="City", department="Dept"):
        self.counselor_id = counselor_id
        self.user_id = user_id
        self.phone_number = phone_number
        self.province = province
        self.city = city
        self.department = department


@pytest.fixture
def mock_db():
    return MagicMock()


def test_get_counselor_by_id_service_found(mock_db):
    mock_counselor = DummyCounselor()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_counselor

    with patch("app.crud.counselors_crud.get_user_by_id", return_value=DummyUser()):
        result = counselors_crud.get_counselor_by_id_service(mock_db, 1)

    assert isinstance(result, schemas.CounselorOut)
    assert result.firstname == "John"
    assert result.phone_number == "12345"


def test_get_counselor_by_id_service_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        counselors_crud.get_counselor_by_id_service(mock_db, 1)
    assert excinfo.value.status_code == 404
    assert "Counselor not found" in excinfo.value.detail


def test_is_admin_true():
    assert counselors_crud.is_admin(schemas.RoleEnum.admin) is True


def test_is_admin_false():
    assert counselors_crud.is_admin(schemas.RoleEnum.student) is False


def test_is_own_data_true():
    assert counselors_crud.is_own_data(1, 1) is True


def test_is_own_data_false():
    assert counselors_crud.is_own_data(1, 2) is False


def test_update_counselor_profile_found(mock_db):
    mock_counselor = DummyCounselor()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_counselor
    update_data = schemas.CounselorUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="99999", province="NewProvince", city="NewCity", department="NewDept")

    result = counselors_crud.update_counselor_profile(mock_db, 1, update_data)
    assert result.phone_number == "99999"
    assert result.province == "NewProvince"


def test_update_counselor_profile_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    result = counselors_crud.update_counselor_profile(mock_db, 1, schemas.CounselorUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="99999", province="NewProvince", city="NewCity", department="NewDept"))
    assert result is None


def test_update_counselor_profile_service_admin(mock_db):
    mock_user = DummyUser(role=schemas.RoleEnum.admin)
    mock_counselor = DummyCounselor()

    with patch("app.crud.counselors_crud.get_user_by_id", return_value=mock_user):
        with patch("app.crud.counselors_crud.get_counselor_by_user_id", return_value=mock_counselor):
            with patch("app.crud.counselors_crud.update_counselor_profile", return_value=mock_counselor):
                with patch("app.crud.counselors_crud.update_user_profile", return_value=mock_user):
                    update_data = schemas.CounselorUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="99999", province="NewProvince", city="NewCity", department="NewDept")
                    result = counselors_crud.update_counselor_profile_service(mock_db, {"sub": 1}, update_data)

    assert isinstance(result, schemas.CounselorUpdate)
    assert result.phone_number == "12345"  # comes from counselor mock


def test_update_counselor_profile_service_permission_denied(mock_db):
    mock_user = DummyUser(userid=1, role=schemas.RoleEnum.student)
    mock_counselor = DummyCounselor(user_id=2)

    with patch("app.crud.counselors_crud.get_user_by_id", return_value=mock_user):
        with patch("app.crud.counselors_crud.get_counselor_by_user_id", return_value=mock_counselor):
            with pytest.raises(HTTPException) as excinfo:
                counselors_crud.update_counselor_profile_service(mock_db, {"sub": 1}, schemas.CounselorUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="99999", province="NewProvince", city="NewCity", department="NewDept"))
    assert excinfo.value.status_code == 403


def test_delete_counselor_found(mock_db):
    mock_counselor = DummyCounselor()
    with patch("app.crud.counselors_crud.get_counselor_by_id", return_value=mock_counselor):
        result = counselors_crud.delete_counselor(mock_db, 1)
    assert result is True


def test_delete_counselor_not_found(mock_db):
    with patch("app.crud.counselors_crud.get_counselor_by_id", return_value=None):
        result = counselors_crud.delete_counselor(mock_db, 1)
    assert result is False
