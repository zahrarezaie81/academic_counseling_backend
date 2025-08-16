import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException
from datetime import date, time
from app import models
from app.crud import appointments_crud


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.mark.asyncio
async def test_create_appointment_success(mock_db):
    mock_slot = MagicMock()
    mock_slot.id = 1
    mock_slot.is_reserved = False
    mock_slot.time_range.date = date(2025, 1, 1)
    mock_slot.time_range.counselor_id = 100
    mock_slot.start_time = time(10, 0)
    mock_slot.end_time = time(11, 0)

    mock_range = MagicMock()
    mock_range.date = date(2025, 1, 1)

    mock_student = MagicMock()
    mock_student.student_id = 200
    mock_student.user_id = 300

    mock_student_user = MagicMock()
    mock_student_user.firstname = "John"
    mock_student_user.lastname = "Doe"

    mock_counselor = MagicMock()
    mock_counselor.user_id = 400

    # Query side effects
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_slot,        # slot
        mock_range,       # range
        mock_slot,        # slot again
        mock_student,     # student
        mock_student_user,  # student user
        mock_counselor    # counselor
    ]

    mock_message_manager = AsyncMock()

    with patch("app.crud.appointments_crud.manager.send_personal_message", mock_message_manager):
        appointment = await appointments_crud.create_appointment(mock_db, 200, 1, notes="Some notes")

    assert mock_slot.is_reserved is True
    mock_db.add.assert_any_call(appointment)
    mock_db.commit.assert_called()
    mock_message_manager.assert_awaited_once()
    assert isinstance(appointment, models.Appointment)


@pytest.mark.asyncio
async def test_create_appointment_slot_not_available(mock_db):
    mock_slot = MagicMock()
    mock_slot.is_reserved = True
    mock_db.query.return_value.filter.return_value.first.return_value = mock_slot

    with pytest.raises(HTTPException) as exc_info:
        await appointments_crud.create_appointment(mock_db, 1, 1)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_appointment_success(mock_db):
    mock_appointment = MagicMock()
    mock_appointment.student_id = 1
    mock_appointment.counselor_id = 2
    mock_appointment.date = date(2025, 1, 1)
    mock_appointment.time = time(10, 0)

    mock_student = MagicMock()
    mock_student.user_id = 300
    mock_student.user.firstname = "StudentF"
    mock_student.user.lastname = "StudentL"

    mock_counselor = MagicMock()
    mock_counselor.user.firstname = "CounselorF"
    mock_counselor.user.lastname = "CounselorL"

    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_appointment,  # appointment
        mock_student,      # student
        mock_counselor     # counselor
    ]

    with patch("app.crud.appointments_crud.manager.send_personal_message", AsyncMock()):
        appointment = await appointments_crud.approve_appointment(mock_db, 1)

    assert appointment.status == models.AppointmentStatus.approved
    mock_db.add.assert_called()
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_approve_appointment_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await appointments_crud.approve_appointment(mock_db, 1)

    assert exc_info.value.status_code == 404


def test_cancel_appointment_success(mock_db):
    mock_appointment = MagicMock()
    mock_slot = MagicMock()
    mock_appointment.slot = mock_slot
    mock_db.query.return_value.filter.return_value.first.return_value = mock_appointment

    result = appointments_crud.cancel_appointment(mock_db, 1)

    assert result is True
    assert mock_slot.is_reserved is False
    mock_db.delete.assert_called_once_with(mock_appointment)
    mock_db.commit.assert_called_once()


def test_cancel_appointment_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        appointments_crud.cancel_appointment(mock_db, 1)

    assert exc_info.value.status_code == 404


def test_get_appointments_by_status_found(mock_db):
    mock_counselor = MagicMock()
    mock_counselor.counselor_id = 10
    mock_db.query.return_value.filter.return_value.first.return_value = mock_counselor

    mock_appointment = MagicMock()
    mock_appointment.id = 1
    mock_appointment.student_id = 2
    mock_appointment.date = date(2025, 1, 1)
    mock_appointment.time = time(10, 0)
    mock_appointment.slot.end_time = time(11, 0)

    mock_student = MagicMock()
    mock_student.user_id = 5

    mock_user = MagicMock()
    mock_user.firstname = "First"
    mock_user.lastname = "Last"

    mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [
        (mock_appointment, mock_student, mock_user)
    ]

    with patch("app.crud.appointments_crud.to_jalali_str", return_value="1403-01-01"):
        result = appointments_crud.get_appointments_by_status(mock_db, 1, models.AppointmentStatus.approved)

    assert len(result) == 1
    assert result[0]["firstname"] == "First"
    assert result[0]["date"] == "1403-01-01"


def test_get_appointments_by_status_no_counselor(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    result = appointments_crud.get_appointments_by_status(mock_db, 1, models.AppointmentStatus.approved)
    assert result == []
