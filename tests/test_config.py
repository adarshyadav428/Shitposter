import pytest
from pydantic import ValidationError

from newsbot.config import Settings


def test_state_backend_normalized_to_lowercase() -> None:
    model = Settings(STATE_BACKEND="SQLITE")
    assert model.state_backend == "sqlite"


def test_state_backend_rejects_invalid_value() -> None:
    with pytest.raises(ValidationError):
        Settings(STATE_BACKEND="invalid")
