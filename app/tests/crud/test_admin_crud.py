import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from app.models import RoleEnum, AppointmentStatus
from app import schemas
from app.crud import admin_crud


@pytest.fixture
def mock_db():
    return MagicMock()


def test_list_users_no_role(mock_db):
    mock_query = mock_db.query.return_value
    mock_query.all.return_value = ["user1", "user2"]

    result = admin_crud.list_users(mock_db)

    mock_db.query.assert_called_once()
    assert result == ["user1", "user2"]


def test_list_users_with_role(mock_db):
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.all.return_value = ["filtered_user"]

    result = admin_crud.list_users(mock_db, RoleEnum.admin)

    mock_query.filter.assert_called_once()
    assert result == ["filtered_user"]


def test_delete_user_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        admin_crud.delete_user(mock_db, 1)

    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail


def test_delete_user_found_with_relations(mock_db):
    mock_user = MagicMock()
    mock_student = MagicMock()
    mock_counselor = MagicMock()

    # first query - user
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_user,  # user
        mock_student,  # student
        mock_counselor  # counselor
    ]

    admin_crud.delete_user(mock_db, 1)

    assert mock_db.delete.call_count == 3
    mock_db.commit.assert_called_once()


def test_update_user_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    user_in = schemas.UserUpdate(
        firstname="John",
        lastname="Doe",
        email="john@example.com"
    )

    with pytest.raises(HTTPException):
        admin_crud.update_user(mock_db, 1, user_in)


def test_update_user_success(mock_db):
    mock_user = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    user_in = schemas.UserUpdate(firstname="John", lastname="Doe", email="john@example.com")

    result = admin_crud.update_user(mock_db, 1, user_in)

    assert mock_user.firstname == "John"
    assert mock_user.lastname == "Doe"
    assert mock_user.email == "john@example.com"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)
    assert result == mock_user


def test_create_user_email_exists(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
    user_in = schemas.UserCreate(
        firstname="Test",
        lastname="User",
        email="test@example.com",
        password="@Securepassword123",
        role=RoleEnum.student
    )

    with pytest.raises(HTTPException) as exc_info:
        admin_crud.create_user(mock_db, user_in)

    assert exc_info.value.status_code == 400
    assert "Email already registered" in exc_info.value.detail


def test_get_students_by_counselor(mock_db):
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.join.return_value.filter.return_value
    mock_filter.all.return_value = ["student1"]

    result = admin_crud.get_students_by_counselor(mock_db, 1)

    assert result == ["student1"]


def test_get_student_grades_by_counselor(mock_db):
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.join.return_value.join.return_value.filter.return_value
    mock_filter.all.return_value = [("John", "Doe", 95)]

    result = admin_crud.get_student_grades_by_counselor(mock_db, 1)

    assert result == [("John", "Doe", 95)]


def test_get_study_plans_finalized(mock_db):
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.all.return_value = ["finalized"]
    result = admin_crud.get_study_plans(mock_db, status="finalized")
    assert result == ["finalized"]


def test_get_appointments_with_status(mock_db):
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.all.return_value = ["approved"]
    result = admin_crud.get_appointments(mock_db, status="approved")
    assert result == ["approved"]


def test_delete_appointment_found(mock_db):
    mock_appointment = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_appointment

    result = admin_crud.delete_appointment_by_id(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(mock_appointment)
    mock_db.commit.assert_called_once()


def test_delete_appointment_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    result = admin_crud.delete_appointment_by_id(mock_db, 1)
    assert result is False


def test_get_admin_dashboard_data(mock_db):
    mock_db.query.return_value.filter.return_value.count.side_effect = [5, 2]

    mock_top_counselors = [
        ("Alice", "Smith", 10),
        ("Bob", "Jones", 8)
    ]
    mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_counselors

    result = admin_crud.get_admin_dashboard_data(mock_db)

    assert result["active_users"] == 5
    assert result["done_appointments_last_week"] == 2
    assert result["top_counselors"][0]["firstname"] == "Alice"
    assert result["top_counselors"][0]["session_count"] == 10
