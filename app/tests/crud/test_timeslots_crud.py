# tests/test_timeslots_crud.py

import pytest
from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, CounselorTimeRange, AvailableTimeSlot
from app.crud import timeslots_crud


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_time_range_with_slots(db_session):
    # Arrange
    counselor_id = 1
    test_date = date(2025, 8, 13)
    from_time = time(9, 0)
    to_time = time(11, 0)
    duration = 30

    # Act
    time_range, slots = timeslots_crud.create_time_range_with_slots(
        db=db_session,
        counselor_id=counselor_id,
        date=test_date,
        from_time=from_time,
        to_time=to_time,
        duration_minutes=duration
    )

    # Assert
    assert isinstance(time_range, CounselorTimeRange)
    assert time_range.counselor_id == counselor_id
    assert len(slots) == 4  # 9-9:30, 9:30-10, 10-10:30, 10:30-11
    for slot in slots:
        assert isinstance(slot, AvailableTimeSlot)
        assert slot.is_reserved is False


def test_check_range_overlap(db_session):
    # Arrange: Create an existing range
    existing_range = CounselorTimeRange(
        counselor_id=1,
        date=date(2025, 8, 13),
        from_time=time(9, 0),
        to_time=time(11, 0),
        duration=30
    )
    db_session.add(existing_range)
    db_session.commit()

    # Act + Assert
    assert timeslots_crud.check_range_overlap(
        db=db_session,
        counselor_id=1,
        date=date(2025, 8, 13),
        from_time=time(10, 0),
        to_time=time(10, 30)
    ) is True

    assert timeslots_crud.check_range_overlap(
        db=db_session,
        counselor_id=1,
        date=date(2025, 8, 13),
        from_time=time(11, 0),
        to_time=time(11, 30)
    ) is False


def test_get_ranges_by_counselor_and_slots(db_session):
    # Arrange
    time_range, slots = timeslots_crud.create_time_range_with_slots(
        db=db_session,
        counselor_id=42,
        date=date(2025, 8, 13),
        from_time=time(9, 0),
        to_time=time(10, 0),
        duration_minutes=30
    )

    # Act
    ranges = timeslots_crud.get_ranges_by_counselor(db_session, 42)
    slots_for_range = timeslots_crud.get_slots_by_range(db_session, time_range.id)

    # Assert
    assert len(ranges) == 1
    assert ranges[0].id == time_range.id
    assert len(slots_for_range) == len(slots)


def test_get_time_ranges_with_slots_for_counselor(db_session):
    # Arrange
    tr1, _ = timeslots_crud.create_time_range_with_slots(
        db=db_session,
        counselor_id=7,
        date=date(2025, 8, 13),
        from_time=time(9, 0),
        to_time=time(10, 0),
        duration_minutes=30
    )
    tr2, _ = timeslots_crud.create_time_range_with_slots(
        db=db_session,
        counselor_id=7,
        date=date(2025, 8, 14),
        from_time=time(13, 0),
        to_time=time(14, 0),
        duration_minutes=30
    )

    # Act
    result = timeslots_crud.get_time_ranges_with_slots_for_counselor(db_session, 7)

    # Assert
    assert len(result) == 2
    for item in result:
        assert "slots" in item
        assert all(isinstance(slot, AvailableTimeSlot) for slot in item["slots"])


def test_delete_range_by_id(db_session):
    # Arrange
    tr, _ = timeslots_crud.create_time_range_with_slots(
        db=db_session,
        counselor_id=5,
        date=date(2025, 8, 13),
        from_time=time(9, 0),
        to_time=time(10, 0),
        duration_minutes=30
    )

    # Act + Assert
    assert timeslots_crud.delete_range_by_id(db_session, tr.id) is True
    assert db_session.query(CounselorTimeRange).count() == 0

    # Deleting again should return False
    assert timeslots_crud.delete_range_by_id(db_session, tr.id) is False
