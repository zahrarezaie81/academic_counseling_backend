from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import crud, schemas
from app.utils.connections import manager
from app.auth import JWTBearer

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        
@router.post("/notify/{user_id}")
async def trigger_notification(user_id: int, message: str):
    await manager.send_personal_message(message, user_id)
    return {"status": "sent"}

@router.post("/", response_model=schemas.NotificationOut)
def send_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    return crud.create_notification(db, notification)

@router.get("/{user_id}", response_model=list[schemas.NotificationOut])
def list_notifications(payload: dict = Depends(JWTBearer()), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    return crud.get_user_notifications(db, user_id)

@router.patch("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = crud.mark_as_read(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.delete("/{notification_id}", response_model=schemas.Message)
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = crud.delete_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"detail": "Notification deleted"}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)