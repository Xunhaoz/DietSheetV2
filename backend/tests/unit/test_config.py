import pytest
from pydantic import ValidationError

from app.config import Settings


def test_rejects_api_token_shorter_than_32_characters(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("API_TOKEN", "x" * 31)

    # Act
    with pytest.raises(ValidationError) as raised:
        Settings()

    # Assert
    assert "api_token" in str(raised.value)


def test_validation_error_does_not_print_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    secret = "real-secret-but-one-char-short!"
    monkeypatch.setenv("API_TOKEN", secret)

    # Act
    with pytest.raises(ValidationError) as raised:
        Settings()

    # Assert
    assert secret not in str(raised.value)


def test_settings_repr_masks_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    secret = "s" * 40
    monkeypatch.setenv("API_TOKEN", secret)

    # Act
    text = repr(Settings())

    # Assert
    assert secret not in text
