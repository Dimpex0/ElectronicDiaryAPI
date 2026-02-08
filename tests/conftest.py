import pytest
from unittest.mock import MagicMock
from datetime import datetime
from auth.models import User, Role, Student, Parent
from classes.models import Class
from subjects.models import Subject
from grades.models import Grade, GradeType

@pytest.fixture
def mock_db():
    mock = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    scalars_mock = MagicMock()

    mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    query_mock.where.return_value = filter_mock

    filter_mock.first.return_value = None
    filter_mock.all.return_value = []

    mock.scalars.return_value = scalars_mock
    scalars_mock.all.return_value = []

    mock.get.return_value = None
    return mock

@pytest.fixture
def auth_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_secret_password",
        full_name="Test User",
        role=Role.STUDENT,
        date_of_birth=datetime(2000, 1, 1)
    )

@pytest.fixture
def teacher_user():
    return User(id=1, email="teacher@test.com", full_name="Teacher One", role=Role.TEACHER)

@pytest.fixture
def principal_user():
    return User(id=2, email="principal@test.com", full_name="Principal One", role=Role.PRINCIPAL)

@pytest.fixture
def student_user():
    student = Student(id=10, email="student@test.com", full_name="Student One", role=Role.STUDENT)
    parent = Parent(id=20, email="parent@school.com")
    student.parents = [parent]
    return student

@pytest.fixture
def parent_user(student_user):
    parent = Parent(id=20, role=Role.PARENT, email="parent@school.com")
    parent.children = [student_user]
    return parent

@pytest.fixture
def sample_class(teacher_user):
    return Class(
        id=100,
        name="10A",
        year=2024,
        teacher_id=teacher_user.id,
        teacher=teacher_user,
        students=[],
        archived=False
    )

@pytest.fixture
def sample_subject(teacher_user):
    return Subject(
        id=100,
        name="Math",
        teacher_id=teacher_user.id,
        teacher=teacher_user,
        students=[],
        archived=False
    )

@pytest.fixture
def sample_grade(student_user):
    return Grade(id=500, student_id=student_user.id, grade=5.0, grade_type=GradeType.EXAM)