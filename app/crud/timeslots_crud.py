from sqlalchemy.orm import Session
from app.models import CounselorTimeRange, AvailableTimeSlot
from datetime import datetime
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def check_range_overlap(db: Session, counselor_id: int, date, from_time, to_time) -> bool:
    return db.query(CounselorTimeRange).filter(
        CounselorTimeRange.counselor_id == counselor_id,
        CounselorTimeRange.date == date,
        CounselorTimeRange.from_time < to_time,
        CounselorTimeRange.to_time > from_time
    ).first() is not None

def create_time_range_with_slots(db: Session, counselor_id: int, date, from_time, to_time, duration_minutes: int):
    time_range = CounselorTimeRange(
        counselor_id=counselor_id,
        date=date,
        from_time=from_time,
        to_time=to_time,
        duration=duration_minutes
    )
    db.add(time_range)
    db.flush()

    current = datetime.combine(date, from_time)
    end = datetime.combine(date, to_time)
    slots = []
    while current + timedelta(minutes=duration_minutes) <= end:
        slot = AvailableTimeSlot(
            range_id=time_range.id,
            start_time=current.time(),
            end_time=(current + timedelta(minutes=duration_minutes)).time(),
            is_reserved=False,
        )
        db.add(slot)
        slots.append(slot)
        current += timedelta(minutes=duration_minutes)

    db.commit()
    return time_range, slots

def get_ranges_by_counselor(db: Session, counselor_id: int):
    return db.query(CounselorTimeRange).filter(CounselorTimeRange.counselor_id == counselor_id).all()

def get_slots_by_range(db: Session, range_id: int):
    return db.query(AvailableTimeSlot).filter(AvailableTimeSlot.range_id == range_id).all()

def delete_range_by_id(db: Session, range_id: int):
    obj = db.query(CounselorTimeRange).filter(CounselorTimeRange.id == range_id).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_slots_by_range(db: Session, range_id: int):
    return db.query(AvailableTimeSlot).filter(AvailableTimeSlot.range_id == range_id).all()

def get_time_ranges_with_slots_for_counselor(db: Session, counselor_id: int):
    ranges = db.query(CounselorTimeRange).filter_by(counselor_id=counselor_id).all()
    result = []
    for range_obj in ranges:
        slots = get_slots_by_range(db, range_obj.id)
        result.append({
            "id": range_obj.id,
            "date": range_obj.date,
            "from_time": range_obj.from_time,
            "to_time": range_obj.to_time,
            "duration": range_obj.duration,
            "slots": slots
        })
    return result
