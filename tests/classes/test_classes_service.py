import pytest
from unittest.mock import AsyncMock, patch
from starlette.exceptions import HTTPException
from auth.models import User, Role
from classes.models import Class
from classes.schemas import (
    CreateClassRequest,
    AddStudentsRequest,
    ChangeClassStatusRequest,
    AddSubjectsRequest
)
from classes.service import (
    create_empty_class,
    add_students_to_class,
    change_class_status,
    add_subjects_to_class
)

@pytest.mark.asyncio
async def test_create_empty_class_success(mock_db, teacher_user):
    with patch("classes.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        request = CreateClassRequest(name="10A", year=2024, user_id=teacher_user.id)

        mock_db.get.return_value = teacher_user
        mock_db.query().filter().first.return_value = None

        new_class = await create_empty_class(request, mock_db)

        assert new_class.name == "10A"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_fm.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_create_empty_class_teacher_not_found(mock_db):
    mock_db.get.return_value = None
    request = CreateClassRequest(name="10A", year=2024, user_id=99)

    with pytest.raises(HTTPException) as exc:
        await create_empty_class(request, mock_db)

    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_create_empty_class_invalid_role(mock_db):
    student = User(id=5, role=Role.STUDENT)
    mock_db.get.return_value = student
    request = CreateClassRequest(name="10A", year=2024, user_id=5)

    with pytest.raises(HTTPException) as exc:
        await create_empty_class(request, mock_db)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_create_empty_class_duplicate(mock_db, teacher_user):
    mock_db.get.return_value = teacher_user
    mock_db.query().filter().first.return_value = Class()

    request = CreateClassRequest(name="10A", year=2024, user_id=teacher_user.id)

    with pytest.raises(HTTPException) as exc:
        await create_empty_class(request, mock_db)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_add_students_to_class_success(mock_db, sample_class, student_user):
    with patch("classes.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        mock_db.get.return_value = sample_class
        mock_db.query().where().all.return_value = [student_user]

        request = AddStudentsRequest(students_ids=[10])

        await add_students_to_class(100, request, mock_db)

        assert student_user in sample_class.students
        mock_db.commit.assert_called_once()
        mock_fm.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_add_students_to_class_not_found(mock_db):
    mock_db.get.return_value = None
    request = AddStudentsRequest(students_ids=[10])

    with pytest.raises(HTTPException) as exc:
        await add_students_to_class(999, request, mock_db)

    assert exc.value.status_code == 404

def test_change_class_status_archive_success(mock_db, sample_class):
    mock_db.get.return_value = sample_class
    request = ChangeClassStatusRequest(status=True)

    result = change_class_status(request, 100, mock_db)

    assert result.archived is True
    mock_db.commit.assert_called_once()

def test_change_class_status_unarchive_duplicate(mock_db, sample_class):
    sample_class.archived = True
    mock_db.get.return_value = sample_class
    mock_db.query().filter().first.return_value = Class(id=200)

    request = ChangeClassStatusRequest(status=False)

    with pytest.raises(HTTPException) as exc:
        change_class_status(request, 100, mock_db)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_add_subjects_to_class_success(mock_db, teacher_user, sample_class, student_user, sample_subject):
    sample_class.students = [student_user]
    mock_db.get.return_value = sample_class
    mock_db.scalars().all.return_value = [sample_subject]

    request = AddSubjectsRequest(subjects_ids=[500])

    await add_subjects_to_class(teacher_user, 100, request, mock_db)

    assert student_user in sample_subject.students
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_add_subjects_to_class_forbidden(mock_db, sample_class):
    other_teacher = User(id=99, role=Role.TEACHER)
    mock_db.get.return_value = sample_class

    request = AddSubjectsRequest(subjects_ids=[500])

    with pytest.raises(HTTPException) as exc:
        await add_subjects_to_class(other_teacher, 100, request, mock_db)

    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_add_subjects_to_class_missing_subject(mock_db, teacher_user, sample_class):
    mock_db.get.return_value = sample_class
    mock_db.scalars().all.return_value = []

    request = AddSubjectsRequest(subjects_ids=[500])

    with pytest.raises(HTTPException) as exc:
        await add_subjects_to_class(teacher_user, 100, request, mock_db)

    assert exc.value.status_code == 404