import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.crud import public_crud
from app import models


# ---------- get_all_counselors ----------
def test_get_all_counselors_returns_list():
    db = MagicMock()
    fake_result = [("c1", "John", "Doe", "img.jpg")]
    db.query.return_value.join.return_value.filter.return_value.all.return_value = fake_result

    result = public_crud.get_all_counselors(db)

    assert result == fake_result
    db.query.assert_called_once()


# ---------- leave_feedback ----------
def test_leave_feedback_success():
    db = MagicMock()

    fake_student = MagicMock(student_id=1)
    fake_appointment = MagicMock()
    fake_feedback = MagicMock()

    # Mock queries
    db.query.return_value.filter.return_value.first.side_effect = [
        fake_student,  # First query: Student found
        fake_appointment  # Second query: Approved appointment found
    ]

    # commit/refresh do nothing
    def add_side_effect(obj):
        assert isinstance(obj, models.Feedback)
    db.add.side_effect = add_side_effect
    db.refresh.side_effect = lambda obj: None

    result = public_crud.leave_feedback(db, 10, 20, rating=5, comment="Great!")

    assert result is not None
    assert isinstance(result, models.Feedback)  # Should be the Feedback object from creation


def test_leave_feedback_student_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        public_crud.leave_feedback(db, 10, 20)

    assert exc.value.status_code == 404
    assert "Student not found" in exc.value.detail


def test_leave_feedback_no_appointment():
    db = MagicMock()
    fake_student = MagicMock(student_id=1)

    # First query returns student, second returns None
    db.query.return_value.filter.return_value.first.side_effect = [
        fake_student, None
    ]

    with pytest.raises(HTTPException) as exc:
        public_crud.leave_feedback(db, 10, 20)

    assert exc.value.status_code == 403
    assert "after an approved appointment" in exc.value.detail


# ---------- get_public_counselor_info ----------
def test_get_public_counselor_info_success():
    db = MagicMock()

    # Fake counselor & user
    fake_user = MagicMock(
        firstname="Jane",
        lastname="Doe",
        email="jane@example.com",
        profile_image_url="url.jpg"
    )
    fake_counselor = MagicMock(
        counselor_id=123,
        user=fake_user,
        phone_number="12345",
        province="SomeProvince",
        city="SomeCity",
        department="Dept"
    )

    # Fake free slots
    class Slot:
        def __init__(self):
            self.id = 1
            self.start_time = __import__("datetime").time(9, 0, 0)
            self.end_time = __import__("datetime").time(10, 0, 0)
            self.date = __import__("datetime").date(2024, 1, 1)
            self.is_reserved = False

    fake_slot = Slot()
    fake_feedbacks = [MagicMock(), MagicMock()]

    # First query: counselor
    # Second query: slots
    # Third query: feedbacks
    db.query.return_value.options.return_value.filter.return_value.first.side_effect = [
        fake_counselor  # counselor found
    ]
    db.query.return_value.join.return_value.filter.return_value.all.side_effect = [
        [fake_slot]  # slots
    ]
    db.query.return_value.filter.return_value.all.side_effect = [
        fake_feedbacks  # feedbacks
    ]

    with patch("app.crud.public_crud.to_jalali_str", return_value="1402-01-01"):
        result = public_crud.get_public_counselor_info(db, 123)

    assert result["counselor_id"] == 123
    assert result["firstname"] == "Jane"
    assert result["free_slots"][0]["date"] == "1402-01-01"
    assert result["feedbacks"] == fake_feedbacks


def test_get_public_counselor_info_not_found():
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        public_crud.get_public_counselor_info(db, 999)

    assert exc.value.status_code == 404
    assert "Counselor not found" in exc.value.detail
