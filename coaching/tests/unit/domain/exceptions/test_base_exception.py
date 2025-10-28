"""Unit tests for base DomainException."""

import pytest
from coaching.src.domain.exceptions.base_exception import DomainException


class TestDomainExceptionCreation:
    """Test suite for DomainException creation."""

    def test_create_with_all_parameters(self) -> None:
        """Test creating exception with all parameters."""
        exc = DomainException(
            message="Test error occurred",
            code="TEST_ERROR",
            context={"key": "value", "count": 42},
        )

        assert exc.message == "Test error occurred"
        assert exc.code == "TEST_ERROR"
        assert exc.context == {"key": "value", "count": 42}

    def test_create_without_context(self) -> None:
        """Test creating exception without context."""
        exc = DomainException(message="Simple error", code="SIMPLE_ERROR")

        assert exc.message == "Simple error"
        assert exc.code == "SIMPLE_ERROR"
        assert exc.context == {}

    def test_exception_inherits_from_exception(self) -> None:
        """Test that DomainException inherits from Exception."""
        exc = DomainException(message="Test", code="TEST")

        assert isinstance(exc, Exception)
        assert isinstance(exc, DomainException)


class TestDomainExceptionStringRepresentation:
    """Test suite for exception string representations."""

    def test_str_without_context(self) -> None:
        """Test __str__ without context."""
        exc = DomainException(message="Error message", code="ERROR_CODE")

        result = str(exc)

        assert result == "[ERROR_CODE] Error message"

    def test_str_with_context(self) -> None:
        """Test __str__ with context."""
        exc = DomainException(message="Error message", code="ERROR_CODE", context={"id": "123"})

        result = str(exc)

        assert "[ERROR_CODE]" in result
        assert "Error message" in result
        assert "Context:" in result
        assert "'id': '123'" in result

    def test_repr(self) -> None:
        """Test __repr__ for debugging."""
        exc = DomainException(message="Test error", code="TEST", context={"data": "value"})

        result = repr(exc)

        assert "DomainException" in result
        assert "message='Test error'" in result
        assert "code='TEST'" in result
        assert "context=" in result


class TestDomainExceptionSerialization:
    """Test suite for exception serialization."""

    def test_to_dict(self) -> None:
        """Test converting exception to dictionary."""
        exc = DomainException(
            message="Test error", code="TEST_ERROR", context={"user_id": "user-123"}
        )

        data = exc.to_dict()

        assert data["error_type"] in ("DomainException", "DomainError")
        assert data["message"] == "Test error"
        assert data["code"] == "TEST_ERROR"
        assert data["context"] == {"user_id": "user-123"}

    def test_to_dict_structure(self) -> None:
        """Test that to_dict returns correct structure."""
        exc = DomainException(message="Error", code="ERR")

        data = exc.to_dict()

        assert "error_type" in data
        assert "message" in data
        assert "code" in data
        assert "context" in data


class TestDomainExceptionRaising:
    """Test suite for raising exceptions."""

    def test_raise_and_catch(self) -> None:
        """Test raising and catching domain exception."""
        with pytest.raises(DomainException) as exc_info:
            raise DomainException(message="Test error", code="TEST")

        exc = exc_info.value
        assert exc.message == "Test error"
        assert exc.code == "TEST"

    def test_raise_with_context(self) -> None:
        """Test raising exception with context data."""
        with pytest.raises(DomainException) as exc_info:
            raise DomainException(
                message="Validation failed",
                code="VALIDATION_ERROR",
                context={"field": "email", "reason": "invalid format"},
            )

        exc = exc_info.value
        assert exc.context["field"] == "email"
        assert exc.context["reason"] == "invalid format"

    def test_catch_as_base_exception(self) -> None:
        """Test catching domain exception as base Exception."""
        with pytest.raises(Exception):
            raise DomainException(message="Error", code="ERR")


class TestDomainExceptionSubclassing:
    """Test suite for creating exception subclasses."""

    def test_create_custom_exception_subclass(self) -> None:
        """Test creating custom exception that inherits from DomainException."""

        class CustomException(DomainException):
            def __init__(self, resource_id: str) -> None:
                super().__init__(
                    message=f"Resource {resource_id} not found",
                    code="RESOURCE_NOT_FOUND",
                    context={"resource_id": resource_id},
                )

        exc = CustomException(resource_id="res-123")

        assert exc.message == "Resource res-123 not found"
        assert exc.code == "RESOURCE_NOT_FOUND"
        assert exc.context["resource_id"] == "res-123"
        assert isinstance(exc, DomainException)

    def test_subclass_to_dict_includes_type(self) -> None:
        """Test that subclass type is included in to_dict."""

        class SpecificError(DomainException):
            def __init__(self) -> None:
                super().__init__(message="Specific error", code="SPECIFIC")

        exc = SpecificError()
        data = exc.to_dict()

        assert data["error_type"] == "SpecificError"
