from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, auth, models
from app.database import get_db
from app.schemas import NotificationCreate

router = APIRouter(
    prefix="/timeslots",
    tags=["timeslots"]
)

@router.post("/", status_code=201)
def create_time_range(
    time_input: schemas.TimeRangeInput,
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    user_id = int(payload.get("sub"))
    counselor = crud.get_counselor_by_user_id(db, user_id)
    user = crud.get_user_by_id(db, user_id)

    if user.role != schemas.RoleEnum.counselor:
        raise HTTPException(403, "Only counselors can create slots")

    if not counselor:
        raise HTTPException(404, "Counselor not found")

    if crud.check_range_overlap(db, counselor.counselor_id, time_input.date, time_input.from_time, time_input.to_time):
        raise HTTPException(400, "Overlapping time range")

    time_range, slots = crud.create_time_range_with_slots(
        db, counselor.counselor_id,
        time_input.date, time_input.from_time, time_input.to_time,
        time_input.duration_minutes
    )

    return {"range_id": time_range.id, "slot_count": len(slots)}


@router.get("/my/", response_model=list[schemas.TimeRangeOut])
def get_my_ranges(
    db: Session = Depends(get_db),
    payload: dict = Depends(auth.JWTBearer())
):
    user_id = int(payload.get("sub"))
    counselor = crud.get_counselor_by_user_id(db, user_id)
    if not counselor:
        raise HTTPException(404, "Counselor not found")

    return crud.get_ranges_by_counselor(db, counselor.counselor_id)

@router.get("/range/", response_model=schemas.TimeRangeWithSlots)
def get_slots_for_range(
    range_id: int,
    db: Session = Depends(get_db)
):
    range_obj = db.query(crud.CounselorTimeRange).filter_by(id=range_id).first()
    if not range_obj:
        raise HTTPException(404, "Time range not found")

    slots = crud.get_slots_by_range(db, range_id)
    return {
        "id": range_obj.id,
        "date": range_obj.date,
        "from_time": range_obj.from_time,
        "to_time": range_obj.to_time,
        "duration": range_obj.duration,
        "slots": slots
    }

@router.delete("/range/{range_id}")
def delete_time_range(range_id: int, db: Session = Depends(get_db)):
    success = crud.delete_range_by_id(db, range_id)
    if not success:
        raise HTTPException(404, "Range not found")
    return {"message": "Time range deleted"}



