import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from starlette.exceptions import HTTPException
from auth.models import User, Role, Parent, Student
from subjects.models import Subject
from grades.models import Grade, GradeType
from grades.schemas import GradeCreateRequest
from grades.service import get_all_grades, get_grade, create_grade

# --- Fixtures ---

@pytest.fixture
def mock_db():
    mock = MagicMock()
    # Mocking db.scalars().all() for get_all_grades
    statement_mock = MagicMock()
    mock.scalars.return_value = statement_mock
    statement_mock.all.return_value = []
    return mock

@pytest.fixture
def teacher_user():
    return User(id=1, role=Role.TEACHER, email="teacher@school.com")

@pytest.fixture
def student_user():
    # Setup Student with parents for email logic
    student = Student(id=10, role=Role.STUDENT, email="student@school.com")
    # Mock parents relationship
    parent = Parent(id=20, email="parent@school.com")
    student.parents = [parent]
    return student

@pytest.fixture
def parent_user(student_user):
    parent = Parent(id=20, role=Role.PARENT, email="parent@school.com")
    # Mock children relationship
    parent.children = [student_user]
    return parent

@pytest.fixture
def sample_subject(teacher_user, student_user):
    subject = Subject(id=100, name="Math", teacher_id=teacher_user.id)

    # FIX: Assign the actual Student object to the relationship list.
    # The 'students_ids' property on the model will calculate automatically from this.
    subject.students = [student_user]

    return subject

@pytest.fixture
def sample_grade(student_user):
    return Grade(id=500, student_id=student_user.id, grade=5.0, grade_type=GradeType.EXAM)

# --- Tests for get_all_grades ---

def test_get_all_grades(mock_db, sample_grade):
    mock_db.scalars().all.return_value = [sample_grade]

    result = get_all_grades(mock_db)

    assert len(result) == 1
    assert result[0].id == 500

# --- Tests for get_grade ---

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
    assert "Can't see that grade" in exc.value.detail

def test_get_grade_parent_success(mock_db, parent_user, sample_grade):
    mock_db.get.return_value = sample_grade
    result = get_grade(parent_user, 500, mock_db)
    assert result == sample_grade

def test_get_grade_parent_forbidden(mock_db, sample_grade):
    other_parent = Parent(id=88, role=Role.PARENT)
    other_parent.children = [] # No children
    mock_db.get.return_value = sample_grade
    with pytest.raises(HTTPException) as exc:
        get_grade(other_parent, 500, mock_db)
    assert exc.value.status_code == 403

# --- Tests for create_grade ---

@pytest.mark.asyncio
async def test_create_grade_success(mock_db, teacher_user, student_user, sample_subject):
    with patch("grades.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        request = GradeCreateRequest(
            student_id=student_user.id,
            subject_id=sample_subject.id,
            grade=5.5,
            # FIX: Use .value to pass the integer (1) instead of the Enum object
            type=GradeType.HOMEWORK.value
        )

        # Mock DB lookups
        def db_get_side_effect(model, id):
            if model == Subject and id == sample_subject.id:
                return sample_subject
            if model == Student and id == student_user.id:
                return student_user
            return None

        mock_db.get.side_effect = db_get_side_effect

        # Act
        new_grade = await create_grade(teacher_user, request, mock_db)

        # Assert
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
    assert "not a teacher of the subject" in exc.value.detail

@pytest.mark.asyncio
async def test_create_grade_student_not_in_subject(mock_db, teacher_user, sample_subject):
    # Subject has student_id 10 (from fixture), request asks for student_id 99
    mock_db.get.return_value = sample_subject
    request = GradeCreateRequest(student_id=99, subject_id=100, grade=5, type=1)

    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request, mock_db)

    assert exc.value.status_code == 403
    assert "Student is not part of the subject" in exc.value.detail

@pytest.mark.asyncio
async def test_create_grade_student_not_found_in_db(mock_db, teacher_user, sample_subject):
    # FIX: We need the service check "if ID in subject.students_ids" to PASS.
    # So we add a dummy student with ID 99 to the subject's list.
    fake_student_in_class = Student(id=99)
    sample_subject.students.append(fake_student_in_class)

    # BUT: We want "db.get(Student, 99)" to return None (FAIL).
    mock_db.get.side_effect = [sample_subject, None]

    request = GradeCreateRequest(student_id=99, subject_id=100, grade=5, type=1)

    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request, mock_db)

    assert exc.value.status_code == 400
    assert "Provided student is not actually a student" in exc.value.detail

@pytest.mark.asyncio
async def test_create_grade_invalid_value(mock_db, teacher_user, sample_subject, student_user):
    mock_db.get.side_effect = [sample_subject, student_user]

    # Grade < 2
    request_low = GradeCreateRequest(student_id=student_user.id, subject_id=100, grade=1, type=1)
    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request_low, mock_db)
    assert exc.value.status_code == 400

    # Grade > 6
    mock_db.get.side_effect = [sample_subject, student_user]
    request_high = GradeCreateRequest(student_id=student_user.id, subject_id=100, grade=7, type=1)
    with pytest.raises(HTTPException) as exc:
        await create_grade(teacher_user, request_high, mock_db)
    assert exc.value.status_code == 400