import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from jose import jwt
from starlette.exceptions import HTTPException
from starlette import status

from auth.models import Role
from auth.schemas import CreateUserRequest, ChangePasswordRequest
from auth.service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    create_user,
    send_email_for_password_change,
    send_email_for_new_user,
    change_password
)

TEST_SECRET_KEY = "test_secret_key"
TEST_ALGORITHM = "HS256"

def test_authenticate_user_success(mock_db, auth_user):
    with patch("auth.service.password_hash") as mock_hash:
        mock_hash.verify.return_value = True
        mock_db.query().filter().first.return_value = auth_user

        result = authenticate_user("test@example.com", "correct_password", mock_db)

        assert result is not None
        assert result.email == "test@example.com"
        mock_hash.verify.assert_called_with("correct_password", "hashed_secret_password")

def test_authenticate_user_wrong_password(mock_db, auth_user):
    with patch("auth.service.password_hash") as mock_hash:
        mock_hash.verify.return_value = False
        mock_db.query().filter().first.return_value = auth_user

        result = authenticate_user("test@example.com", "wrong_password", mock_db)

        assert result is None

def test_authenticate_user_not_found(mock_db):
    mock_db.query().filter().first.return_value = None

    result = authenticate_user("unknown@example.com", "any_password", mock_db)

    assert result is None

def test_create_access_token():
    with patch("auth.service.SECRET_KEY", TEST_SECRET_KEY), \
            patch("auth.service.ALGORITHM", TEST_ALGORITHM), \
            patch("auth.service.ACCESS_TOKEN_EXPIRATION_MINUTES", 30):

        token = create_access_token("test@example.com", 1)

        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert decoded["sub"] == "test@example.com"
        assert decoded["id"] == 1
        assert "exp" in decoded

def test_get_current_user_valid(mock_db, auth_user):
    with patch("auth.service.SECRET_KEY", TEST_SECRET_KEY), \
            patch("auth.service.ALGORITHM", TEST_ALGORITHM):

        token = jwt.encode({"sub": "test@example.com", "id": 1}, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

        mock_db.query().filter().first.return_value = auth_user

        result = get_current_user(token, mock_db)

        assert result.id == 1
        assert result.email == "test@example.com"

def test_get_current_user_invalid_token(mock_db):
    with patch("auth.service.SECRET_KEY", TEST_SECRET_KEY), \
            patch("auth.service.ALGORITHM", TEST_ALGORITHM):

        token = jwt.encode({"sub": "test", "id": 1}, "wrong_key", algorithm=TEST_ALGORITHM)

        with pytest.raises(HTTPException) as exc:
            get_current_user(token, mock_db)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate user" in exc.value.detail

def test_create_user_success(mock_db):
    with patch("auth.service.password_hash") as mock_hash:
        mock_hash.hash.return_value = "new_hashed_pass"
        mock_db.query().filter().first.return_value = None

        request = CreateUserRequest(
            email="new@example.com",
            password="password123",
            full_name="New User",
            role=Role.STUDENT.value,
            date_of_birth=datetime(2000, 1, 1)
        )

        result = create_user(request, mock_db)

        assert result.email == "new@example.com"
        assert result.hashed_password == "new_hashed_pass"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

def test_create_user_duplicate_email(mock_db, auth_user):
    mock_db.query().filter().first.return_value = auth_user

    request = CreateUserRequest(
        email="test@example.com",
        password="pass",
        full_name="Dup",
        role=Role.STUDENT.value,
        date_of_birth=datetime.now()
    )

    with pytest.raises(HTTPException) as exc:
        create_user(request, mock_db)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in exc.value.detail

@pytest.mark.asyncio
async def test_send_emails():
    with patch("auth.service.fm") as mock_fm:
        mock_fm.send_message = AsyncMock()

        await send_email_for_password_change("test@test.com", "token123")
        assert mock_fm.send_message.call_count == 1

        await send_email_for_new_user("test@test.com", "Name", "pass")
        assert mock_fm.send_message.call_count == 2

def test_change_password_success(mock_db, auth_user):
    with patch("auth.service.SECRET_KEY", TEST_SECRET_KEY), \
            patch("auth.service.ALGORITHM", TEST_ALGORITHM), \
            patch("auth.service.password_hash") as mock_hash:

        token = jwt.encode({"id": 1}, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        request = ChangePasswordRequest(old_password="old_pass", new_password="new_pass")

        mock_db.get.return_value = auth_user
        mock_hash.hash.side_effect = lambda x: "hashed_secret_password" if x == "old_pass" else "new_hashed_value"

        change_password(token, request, mock_db)

        assert auth_user.hashed_password == "new_hashed_value"
        mock_db.add.assert_called_with(auth_user)
        mock_db.commit.assert_called_once()

def test_change_password_invalid_token(mock_db):
    with patch("auth.service.SECRET_KEY", TEST_SECRET_KEY), \
            patch("auth.service.ALGORITHM", TEST_ALGORITHM):

        with pytest.raises(HTTPException) as exc:
            change_password("invalid_token_string", ChangePasswordRequest(old_password="a", new_password="b"), mock_db)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED