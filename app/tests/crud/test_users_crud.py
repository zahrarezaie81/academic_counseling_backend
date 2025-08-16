import io
import pytest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import UploadFile

from app import models, schemas, auth
from app.crud import users_crud


@pytest.fixture(scope="function")
def db_session():
    """Fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user_data():
    return schemas.UserCreate(
        firstname="John",
        lastname="Doe",
        email="john@example.com",
        password="@Secret123",
        role=models.RoleEnum.student
    )


def test_create_and_get_user(db_session, user_data):
    user = users_crud.create_user(db_session, user_data)
    assert user.userid is not None
    assert user.email == user_data.email

    fetched_by_email = users_crud.get_user_by_email(db_session, user_data.email)
    fetched_by_id = users_crud.get_user_by_id(db_session, user.userid)
    assert fetched_by_email.userid == user.userid
    assert fetched_by_id.userid == user.userid


def test_create_user_duplicate_email_returns_none(db_session, user_data):
    users_crud.create_user(db_session, user_data)
    duplicate = users_crud.create_user(db_session, user_data)
    assert duplicate is None


def test_authenticate_user_success_and_fail(db_session, user_data):
    users_crud.create_user(db_session, user_data)
    assert users_crud.authenticate_user(db_session, user_data.email, "@Secret123") is not None
    assert users_crud.authenticate_user(db_session, user_data.email, "wrong") is None
    assert users_crud.authenticate_user(db_session, "notfound@example.com", "@Secret123") is None


def test_change_user_password_and_update_user_password(db_session, user_data):
    user = users_crud.create_user(db_session, user_data)

    assert users_crud.change_user_password(db_session, user.email, "newpass") is True
    updated = users_crud.update_user_password(db_session, user.userid, "anotherpass")
    assert auth.verify_password("anotherpass", updated.password_hash)

    # Non-existing user
    assert users_crud.change_user_password(db_session, "missing@example.com", "pass") is False


def test_update_user_role(db_session, user_data):
    user = users_crud.create_user(db_session, user_data)
    updated = users_crud.update_user_role(db_session, user.userid, models.RoleEnum.counselor)
    assert updated.role == models.RoleEnum.counselor


def test_delete_user(db_session, user_data):
    user = users_crud.create_user(db_session, user_data)
    assert users_crud.delete_user(db_session, user.userid) is True
    assert users_crud.delete_user(db_session, user.userid) is False  # already deleted


def test_update_user_profile(db_session, user_data):
    user = users_crud.create_user(db_session, user_data)
    update_data = schemas.StudentUpdate(
        firstname="John",
        lastname="Doe",
        email="john@example.com",
        phone_number="999",
        province="newProvince",
        city="newCity",
        education_year="2025",
        field_of_study="Computer",
        semester_or_year="Fall",
        gpa=192.4848569
    )
    updated = users_crud.update_user_profile(db_session, user.userid, update_data)
    assert updated.firstname == "John"
    assert updated.lastname == "Doe"
    assert updated.email == "john@example.com"

    with pytest.raises(Exception):
        users_crud.update_user_profile(db_session, 999, update_data)


@patch("app.crud.users_crud.upload_file_to_s3", return_value="profile.jpg")
def test_update_user_profile_with_image(mock_upload, db_session, user_data):
    user = users_crud.create_user(db_session, user_data)

    fake_file = UploadFile(filename="profile.jpg", file=io.BytesIO(b"fake image content"))

    updated = users_crud.update_user_profile_with_image(db_session, user.userid, fake_file)
    assert updated.profile_image_filename == "profile.jpg"
    assert updated.profile_image_url.endswith("/profile.jpg")
    mock_upload.assert_called_once()
