
from app.services.password import hash_password, verify_password


def test_password_is_hashed():
    password = "TestPassword123"

    hashed = hash_password(password)

    assert hashed != password


def test_correct_password_is_verified():
    password = "TestPassword123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_incorrect_password_is_rejected():
    hashed = hash_password("TestPassword123")

    assert verify_password("WrongPassword123", hashed) is False


def test_password_hashes_are_different():
    password = "TestPassword123"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
