import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.crud import students_crud
from app import schemas


# ---------- get_student_by_user_id / get_student_by_id ----------
def test_get_student_by_user_id_and_id():
    db = MagicMock()
    fake_student = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = fake_student

    assert students_crud.get_student_by_user_id(db, 1) == fake_student
    assert students_crud.get_student_by_id(db, 2) == fake_student


# ---------- get_student_info ----------
def test_get_student_info_success():
    db = MagicMock()
    fake_user = MagicMock(
        firstname="John",
        lastname="Doe",
        email="j@x.com",
        profile_image_url="img.jpg"
    )
    fake_student = MagicMock(
        student_id=10,
        phone_number="123",
        province="SomeProvince",
        city="SomeCity",
        educational_level="Year 1",
        field_of_study="Science",
        semester_or_year="First",
        gpa=3.5
    )
    with patch.object(students_crud.crud, "get_user_by_id", return_value=fake_user), \
         patch.object(students_crud, "get_student_by_user_id", return_value=fake_student):

        payload = {"sub": "42"}
        result = students_crud.get_student_info(db, payload)

    assert isinstance(result, schemas.StudentOut)
    assert result.firstname == "John"


def test_get_student_info_student_not_found():
    db = MagicMock()
    with patch.object(students_crud.crud, "get_user_by_id", return_value=MagicMock()), \
         patch.object(students_crud, "get_student_by_user_id", return_value=None):

        with pytest.raises(HTTPException) as exc:
            students_crud.get_student_info(db, {"sub": "42"})

    assert exc.value.status_code == 404


# ---------- update_student_profile ----------
def test_update_student_profile_success():
    db = MagicMock()
    fake_student = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = fake_student
    student_in = schemas.StudentUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="999", province="newProvince", city="newCity", education_year="2025", field_of_study="Computer", semester_or_year="Fall", gpa=192.4848569)

    result = students_crud.update_student_profile(db, 10, student_in)

    assert result == fake_student
    db.commit.assert_called_once()


def test_update_student_profile_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        students_crud.update_student_profile(db, 10, schemas.StudentUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="999", province="newProvince", city="newCity", education_year="2025", field_of_study="Computer", semester_or_year="Fall", gpa=192.4848569))

    assert exc.value.status_code == 404


# ---------- is_admin / is_own_data ----------
def test_is_admin_and_is_own_data():
    assert students_crud.is_admin(schemas.RoleEnum.admin) is True
    assert students_crud.is_admin(schemas.RoleEnum.student) is False
    assert students_crud.is_own_data(1, 1) is True
    assert students_crud.is_own_data(1, 2) is False


# ---------- update_student_profile_service ----------
from types import SimpleNamespace
def test_update_student_profile_service_success_as_admin():
    db = MagicMock()

    fake_student = SimpleNamespace(
        student_id=1,
        user_id=5,
        phone_number="12345",
        province="SomeProvince",
        city="SomeCity",
        educational_level="2025",
        field_of_study="Computer",
        semester_or_year="Fall",
        gpa=3.5
    )

    fake_user = SimpleNamespace(
        role=schemas.RoleEnum.admin,
        firstname="John",
        lastname="Doe",
        email="john@example.com"
    )

    with patch.object(students_crud.crud, "get_user_by_id", return_value=fake_user), \
         patch.object(students_crud, "get_student_by_user_id", return_value=fake_student), \
         patch.object(students_crud, "update_student_profile", return_value=fake_student), \
         patch.object(students_crud.crud, "update_user_profile", return_value=fake_user):

        student_in = schemas.StudentUpdate(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            phone_number="999",
            province="newProvince",
            city="newCity",
            education_year="2025",
            field_of_study="Computer",
            semester_or_year="Fall",
            gpa=3.8
        )

        result = students_crud.update_student_profile_service(db, {"sub": "5"}, student_in)

        assert result.firstname == "John"
        assert result.lastname == "Doe"
        assert result.phone_number == "12345"


def test_update_student_profile_service_permission_denied():
    db = MagicMock()
    fake_student = MagicMock(student_id=1, user_id=99)
    fake_user = MagicMock(role=schemas.RoleEnum.student)

    with patch.object(students_crud.crud, "get_user_by_id", return_value=fake_user), \
         patch.object(students_crud, "get_student_by_user_id", return_value=fake_student):

        with pytest.raises(HTTPException) as exc:
            students_crud.update_student_profile_service(db, {"sub": "5"}, schemas.StudentUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="999", province="newProvince", city="newCity", education_year="2025", field_of_study="Computer", semester_or_year="Fall", gpa=192.4848569))

    assert exc.value.status_code == 403


def test_update_student_profile_service_student_not_found():
    db = MagicMock()
    fake_user = MagicMock(role=schemas.RoleEnum.student)

    with patch.object(students_crud.crud, "get_user_by_id", return_value=fake_user), \
         patch.object(students_crud, "get_student_by_user_id", return_value=None):

        with pytest.raises(HTTPException) as exc:
            students_crud.update_student_profile_service(db, {"sub": "5"}, schemas.StudentUpdate(firstname="John", lastname="Doe", email="john@example.com", phone_number="999", province="newProvince", city="newCity", education_year="2025", field_of_study="Computer", semester_or_year="Fall", gpa=192.4848569))

    assert exc.value.status_code == 404


# ---------- delete_student ----------
def test_delete_student_found_and_not_found():
    db = MagicMock()
    fake_student = MagicMock()
    with patch.object(students_crud, "get_student_by_id", return_value=fake_student):
        assert students_crud.delete_student(db, 1) is True
        db.delete.assert_called_once_with(fake_student)

    with patch.object(students_crud, "get_student_by_id", return_value=None):
        assert students_crud.delete_student(db, 1) is False


# ---------- get_progress_percentage ----------
class FakeActivity:
    def __init__(self, status):
        self.status = status

class FakePlan:
    def __init__(self, activities):
        self.activities = activities

def test_get_progress_percentage_no_plan_or_empty():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    assert students_crud.get_progress_percentage(db, 1) == 0.0

    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = FakePlan([])
    assert students_crud.get_progress_percentage(db, 1) == 0.0

def test_get_progress_percentage_with_activities():
    db = MagicMock()
    activities = [FakeActivity("done"), FakeActivity("pending"), FakeActivity("done")]
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = FakePlan(activities)
    assert students_crud.get_progress_percentage(db, 1) == round((2/3)*100, 2)


# ---------- get_recommendations_for_student ----------
def test_get_recommendations_for_student():
    db = MagicMock()
    fake_recs = [MagicMock(), MagicMock()]
    db.query.return_value.filter.return_value.all.return_value = fake_recs
    result = students_crud.get_recommendations_for_student(db, 1)
    assert result == fake_recs


# ---------- get_user_by_student_id ----------
def test_get_user_by_student_id_found_and_not_found():
    db = MagicMock()
    fake_student = MagicMock(user_id=5)
    fake_user = MagicMock()

    db.query.return_value.filter_by.return_value.first.side_effect = [
        fake_student,  # first call (student)
        fake_user      # second call (user)
    ]
    assert students_crud.get_user_by_student_id(db, 1) == fake_user

    db.query.return_value.filter_by.return_value.first.side_effect = [
        None  # student not found
    ]
    assert students_crud.get_user_by_student_id(db, 1) is None
