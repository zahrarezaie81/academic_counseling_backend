from sqlalchemy.orm import Session
from app.models import Notification
from app.schemas import NotificationCreate
from app.utils.connections import manager

async def create_notification(db: Session, notification: NotificationCreate):
    db_item = Notification(**notification.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    await manager.send_personal_message(
        f"New notification: {db_item.message}", db_item.user_id
    )

    return db_item

def get_user_notifications(db: Session, user_id: int):
    return db.query(Notification).filter(Notification.user_id == user_id).all()

def mark_as_read(db: Session, notification_id: int):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.read = True
        db.commit()
        db.refresh(notification)
    return notification

def delete_notification(db: Session, notification_id: int):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        db.delete(notification)
        db.commit()
    return notification