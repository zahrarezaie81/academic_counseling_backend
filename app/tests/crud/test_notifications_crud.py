import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Notification
from app.schemas import NotificationCreate
from app.crud import notifications_crud


# ---------- Database fixture ----------
@pytest.fixture(scope="module")
def db_session():
    # In-memory SQLite that persists for the test session
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


# ---------- Async fixture for mocking manager ----------
@pytest_asyncio.fixture
async def mock_manager_send():
    with patch.object(notifications_crud.manager, "send_personal_message", new=AsyncMock()) as mock_send:
        yield mock_send


# ---------- Tests ----------
@pytest.mark.asyncio
async def test_create_notification(db_session, mock_manager_send):
    notification_data = NotificationCreate(user_id=1, message="Hello World")
    result = await notifications_crud.create_notification(db_session, notification_data)

    # Check DB insertion
    assert result.id is not None
    assert result.user_id == 1
    assert result.message == "Hello World"

    # Check async call to manager
    mock_manager_send.assert_awaited_once_with(
        "New notification: Hello World", 1
    )
    
@pytest.fixture(autouse=True)
def clean_notifications(db_session):
    yield
    db_session.query(Notification).delete()
    db_session.commit()


def test_get_user_notifications(db_session):
    # Insert two notifications for user 1 and one for user 2
    db_session.add_all([
        Notification(user_id=1, message="First"),
        Notification(user_id=1, message="Second"),
        Notification(user_id=2, message="Other")
    ])
    db_session.commit()

    results = notifications_crud.get_user_notifications(db_session, user_id=1)
    assert len(results) == 2
    assert all(n.user_id == 1 for n in results)

@pytest.fixture(autouse=True)
def clean_notifications(db_session):
    yield
    db_session.query(Notification).delete()
    db_session.commit()

def test_mark_as_read(db_session):
    # Create unread notification
    notif = Notification(user_id=3, message="Read me", read=False)
    db_session.add(notif)
    db_session.commit()

    updated = notifications_crud.mark_as_read(db_session, notif.id)
    assert updated.read is True

    # Test non-existent notification
    assert notifications_crud.mark_as_read(db_session, 99999) is None

@pytest.fixture(autouse=True)
def clean_notifications(db_session):
    yield
    db_session.query(Notification).delete()
    db_session.commit()

def test_delete_notification(db_session):
    notif = Notification(user_id=4, message="To delete")
    db_session.add(notif)
    db_session.commit()
    notif_id = notif.id

    deleted = notifications_crud.delete_notification(db_session, notif_id)
    assert deleted.id == notif_id

    # Ensure it’s removed
    assert db_session.query(Notification).filter_by(id=notif_id).first() is None

    # Test deleting a non-existent one
    assert notifications_crud.delete_notification(db_session, 99999) is None

@pytest.fixture(autouse=True)
def clean_notifications(db_session):
    yield
    db_session.query(Notification).delete()
    db_session.commit()