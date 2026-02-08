import pytest
from unittest.mock import AsyncMock, patch
from starlette.exceptions import HTTPException
from auth.models import User, Role
from subjects.models import Subject
from subjects.schemas import (
    CreateSubjectRequest,
    AddStudentsRequest,
    RemoveStudentsRequest,
    StatusRequest,
    TeacherRequest
)
from subjects.service import (
    create_subject,
    add_students,
    remove_students,
    change_status,
    change_teacher
)

@pytest.mark.asyncio
async def test_create_subject_success(mock_db, teacher_user, student_user):
    with patch("subjects.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        request = CreateSubjectRequest(name="Math", teacher_id=teacher_user.id, students_ids=[10])

        mock_db.get.return_value = teacher_user
        mock_db.query().filter().first.return_value = None
        mock_db.scalars().all.return_value = [student_user]

        result = await create_subject(teacher_user, request, mock_db)

        assert result.name == "Math"
        assert result.teacher_id == teacher_user.id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert mock_fm.send_message.call_count == 2

@pytest.mark.asyncio
async def test_create_subject_forbidden_wrong_teacher(mock_db):
    user = User(id=99, role=Role.TEACHER)
    request = CreateSubjectRequest(name="Math", teacher_id=1, students_ids=[])

    with pytest.raises(HTTPException) as exc:
        await create_subject(user, request, mock_db)

    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_create_subject_duplicate(mock_db, teacher_user):
    request = CreateSubjectRequest(name="Math", teacher_id=teacher_user.id, students_ids=[])
    mock_db.query().filter().first.return_value = Subject()

    with pytest.raises(HTTPException) as exc:
        await create_subject(teacher_user, request, mock_db)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_create_subject_assigned_user_not_teacher(mock_db, principal_user):
    request = CreateSubjectRequest(name="Math", teacher_id=5, students_ids=[])
    student_role = User(id=5, role=Role.STUDENT)

    mock_db.query().filter().first.return_value = None
    mock_db.get.return_value = student_role

    with pytest.raises(HTTPException) as exc:
        await create_subject(principal_user, request, mock_db)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_add_students_success(mock_db, teacher_user, student_user, sample_subject):
    with patch("subjects.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        request = AddStudentsRequest(students_ids=[student_user.id])
        mock_db.get.return_value = sample_subject
        mock_db.scalars().all.return_value = [student_user]

        await add_students(teacher_user, request, sample_subject.id, mock_db)

        assert student_user in sample_subject.students
        mock_db.commit.assert_called_once()
        mock_fm.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_add_students_subject_not_found(mock_db, teacher_user):
    mock_db.get.return_value = None
    request = AddStudentsRequest(students_ids=[1])

    with pytest.raises(HTTPException) as exc:
        await add_students(teacher_user, request, 999, mock_db)

    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_remove_students_success(mock_db, teacher_user, student_user, sample_subject):
    with patch("subjects.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        sample_subject.students = [student_user]
        mock_db.get.return_value = sample_subject
        mock_db.scalars().all.return_value = [student_user]

        request = RemoveStudentsRequest(students_ids=[student_user.id])

        await remove_students(teacher_user, request, sample_subject.id, mock_db)

        assert student_user not in sample_subject.students
        mock_db.commit.assert_called_once()
        mock_fm.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_change_status_archive_success(mock_db, teacher_user, sample_subject):
    with patch("subjects.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        mock_db.get.return_value = sample_subject
        request = StatusRequest(status=True)

        result = await change_status(teacher_user, sample_subject.id, request, mock_db)

        assert result.archived is True
        mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_change_status_unarchive_duplicate(mock_db, teacher_user, sample_subject):
    sample_subject.archived = True
    mock_db.get.return_value = sample_subject
    mock_db.query().filter().first.return_value = Subject(id=200)

    request = StatusRequest(status=False)

    with pytest.raises(HTTPException) as exc:
        await change_status(teacher_user, sample_subject.id, request, mock_db)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_change_teacher_success(mock_db, sample_subject):
    with patch("subjects.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        new_teacher = User(id=5, email="new@test.com", full_name="New T", role=Role.TEACHER)
        mock_db.get.side_effect = [sample_subject, new_teacher]
        mock_db.query().filter().first.return_value = None

        request = TeacherRequest(teacher_id=5)

        result = await change_teacher(request, sample_subject.id, mock_db)

        assert result.teacher_id == 5
        mock_db.commit.assert_called_once()
        mock_fm.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_change_teacher_duplicate_assignment(mock_db, sample_subject):
    new_teacher = User(id=5, role=Role.TEACHER)
    mock_db.get.side_effect = [sample_subject, new_teacher]
    mock_db.query().filter().first.return_value = Subject()

    request = TeacherRequest(teacher_id=5)

    with pytest.raises(HTTPException) as exc:
        await change_teacher(request, sample_subject.id, mock_db)

    assert exc.value.status_code == 400