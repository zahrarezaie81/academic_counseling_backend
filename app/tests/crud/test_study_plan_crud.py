# tests/test_study_plan_crud.py

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException
from datetime import datetime

from app.crud import study_plan_crud
from app.models import StudyPlan, StudyActivity, Student, Counselor, User, Notification, Recommendation
from app.schemas import ActivityStatusUpdate, StudyPlanCreate


@pytest.mark.asyncio
async def test_create_study_plan_success():
    db = MagicMock()

    mock_counselor = Counselor(counselor_id=1, user_id=10)
    mock_student = Student(student_id=2, user_id=20)
    mock_user = User(userid=10, firstname="John", lastname="Doe")

    db.query().filter().first.side_effect = [
        mock_counselor,  # counselor found
        mock_student     # student found
    ]
    db.query().get.return_value = mock_user

    mock_data = MagicMock()
    mock_data.student_id = 2
    mock_data.activities = []

    with patch("app.crud.study_plan_crud.manager.send_personal_message", new_callable=AsyncMock):
        result = await study_plan_crud.create_study_plan(db, 10, mock_data)

    assert isinstance(result, StudyPlan)
    db.add.assert_any_call(result)
    db.commit.assert_called()


@pytest.mark.asyncio
async def test_create_study_plan_no_counselor():
    db = MagicMock()
    db.query().filter().first.return_value = None

    mock_data = MagicMock()
    mock_data.student_id = 2

    with pytest.raises(HTTPException) as exc:
        await study_plan_crud.create_study_plan(db, 10, mock_data)
    assert exc.value.status_code == 404
    assert "Counselor not found" in exc.value.detail


def test_finalize_plan_success():
    db = MagicMock()
    plan = StudyPlan(plan_id=1, is_finalized=False)
    db.query().filter().first.return_value = plan

    study_plan_crud.finalize_plan(db, 1)

    assert plan.is_finalized is True
    db.commit.assert_called_once()


def test_finalize_plan_not_found():
    db = MagicMock()
    db.query().filter().first.return_value = None

    with pytest.raises(HTTPException):
        study_plan_crud.finalize_plan(db, 999)


def test_get_student_weekly_plan_none_found():
    db = MagicMock()
    db.query().filter().first.return_value = None  # no student

    with pytest.raises(HTTPException):
        study_plan_crud.get_student_weekly_plan(db, 123)


def test_update_activity_status_success():
    db = MagicMock()
    db.query().filter().first.return_value = Student(student_id=2)

    mock_activity = StudyActivity(activity_id=1, status="pending", student_note=None)
    db.query().join().filter().first.return_value = mock_activity

    updates = [ActivityStatusUpdate(activity_id=1, status="done", student_note="ok")]

    study_plan_crud.update_activity_status(db, 1, updates)

    assert mock_activity.status == "done"
    assert mock_activity.student_note == "ok"
    db.commit.assert_called_once()


def test_update_activity_status_student_not_found():
    db = MagicMock()
    db.query().filter().first.return_value = None

    with pytest.raises(HTTPException):
        study_plan_crud.update_activity_status(db, 1, [])


def test_student_submit_status_success():
    db = MagicMock()
    student = Student(student_id=2)
    plan = StudyPlan(plan_id=1, is_finalized=True)

    # Mock the first query for student
    db.query().filter.return_value.first.side_effect = [student]

    # Mock the second query for plan
    db.query().filter().order_by.return_value.first.return_value = plan

    study_plan_crud.student_submit_status(db, 1)

    assert plan.is_submitted_by_student is True
    assert plan.student_submit_time is not None
    db.commit.assert_called_once()


def test_set_plan_score_success():
    db = MagicMock()
    plan = StudyPlan(plan_id=1, is_submitted_by_student=True)
    db.query().filter().first.return_value = plan

    result = study_plan_crud.set_plan_score(db, 1, 95)

    assert plan.score == 95
    assert result == {"detail": "Score saved"}


def test_set_plan_score_not_found():
    db = MagicMock()
    db.query().filter().first.return_value = None

    with pytest.raises(HTTPException):
        study_plan_crud.set_plan_score(db, 1, 95)


def test_create_recommendation_success():
    db = MagicMock()
    rec = study_plan_crud.create_recommendation(db, 1, 2, "Math")
    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert isinstance(rec, Recommendation)
