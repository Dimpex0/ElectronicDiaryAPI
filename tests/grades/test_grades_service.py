import pytest
from unittest.mock import AsyncMock, patch
from starlette.exceptions import HTTPException
from auth.models import User, Role, Student, Parent
from subjects.models import Subject
from grades.models import Grade, GradeType
from grades.schemas import GradeCreateRequest
from grades.service import get_all_grades, get_grade, create_grade

def test_get_all_grades(mock_db, sample_grade):
    mock_db.scalars().all.return_value = [sample_grade]
    result = get_all_grades(mock_db)
    assert len(result) == 1
    assert result[0].id == 500

def test_get_grade_success_teacher(mock_db, teacher_user, sample_grade):
    mock_db.get.return_value = sample_grade
    result = get_grade(teacher_user, 500, mock_db)
    assert result == sample_grade

def test_get_grade_not_found(mock_db, teacher_user):
    mock_db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_grade(teacher_user, 999, mock_db)
    assert exc.value.status_code == 404

def test_get_grade_student_success(mock_db, student_user, sample_grade):
    mock_db.get.return_value = sample_grade
    result = get_grade(student_user, 500, mock_db)
    assert result == sample_grade

def test_get_grade_student_forbidden(mock_db, sample_grade):
    other_student = User(id=99, role=Role.STUDENT)
    mock_db.get.return_value = sample_grade
    with pytest.raises(HTTPException) as exc:
        get_grade(other_student, 500, mock_db)
    assert exc.value.status_code == 403

def test_get_grade_parent_success(mock_db, parent_user, sample_grade):
    mock_db.get.return_value = sample_grade
    result = get_grade(parent_user, 500, mock_db)
    assert result == sample_grade

def test_get_grade_parent_forbidden(mock_db, sample_grade):
    other_parent = Parent(id=88, role=Role.PARENT)
    other_parent.children = []
    mock_db.get.return_value = sample_grade
    with pytest.raises(HTTPException) as exc:
        get_grade(other_parent, 500, mock_db)
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_create_grade_success(mock_db, teacher_user, student_user, sample_subject):
    with patch("grades.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        sample_subject.students = [student_user]

        request = GradeCreateRequest(
            student_id=student_user.id,
            subject_id=sample_subject.id,
            grade=5.5,
            type=GradeType.HOMEWORK.value
        )

        def db_get_side_effect(model, id):
            if model == Subject and id == sample_subject.id:
                return sample_subject
            if model == Student and id == student_user.id:
                return student_user
            return None

        mock_db.get.side_effect = db_get_side_effect

        new_grade = await create_grade(teacher_user, request, mock_db)

        assert new_grade.grade == 5.5
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_fm.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_create_grade_subject_not_found(mock_db, teacher_user):
    mock_db.get.return_value = None
    request = GradeCreateRequest(student_id=1, subject_id=999, grade=5, type=1)

    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request, mock_db)

    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_create_grade_teacher_forbidden(mock_db, sample_subject, student_user):
    other_teacher = User(id=99, role=Role.TEACHER)
    mock_db.get.return_value = sample_subject

    request = GradeCreateRequest(student_id=student_user.id, subject_id=100, grade=5, type=1)

    with pytest.raises(HTTPException) as exc:
        await create_grade(other_teacher, request, mock_db)

    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_create_grade_student_not_in_subject(mock_db, teacher_user, sample_subject):
    mock_db.get.return_value = sample_subject
    request = GradeCreateRequest(student_id=99, subject_id=100, grade=5, type=1)

    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request, mock_db)

    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_create_grade_student_not_found_in_db(mock_db, teacher_user, sample_subject):
    fake_student_in_class = Student(id=99)
    sample_subject.students.append(fake_student_in_class)

    mock_db.get.side_effect = [sample_subject, None]

    request = GradeCreateRequest(student_id=99, subject_id=100, grade=5, type=1)

    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request, mock_db)

    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_create_grade_invalid_value(mock_db, teacher_user, sample_subject, student_user):
    sample_subject.students = [student_user]
    mock_db.get.side_effect = [sample_subject, student_user]

    request_low = GradeCreateRequest(student_id=student_user.id, subject_id=100, grade=1, type=1)
    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request_low, mock_db)
    assert exc.value.status_code == 400

    mock_db.get.side_effect = [sample_subject, student_user]
    request_high = GradeCreateRequest(student_id=student_user.id, subject_id=100, grade=7, type=1)
    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request_high, mock_db)
    assert exc.value.status_code == 400