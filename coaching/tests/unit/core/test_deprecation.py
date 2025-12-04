import pytest
from coaching.src.core.deprecation import deprecated

pytestmark = pytest.mark.unit


class TestDeprecation:
    """Test suite for deprecation utilities."""

    def test_deprecated_function_warning(self):
        """Test that calling a deprecated function issues a warning."""

        @deprecated("This function is deprecated", alternative="new_func", removal_version="2.0.0")
        def old_func():
            return "result"

        with pytest.warns(
            DeprecationWarning, match="DEPRECATED: old_func - This function is deprecated"
        ):
            result = old_func()
            assert result == "result"

    def test_deprecated_class_warning(self):
        """Test that instantiating a deprecated class issues a warning."""

        @deprecated("This class is deprecated", alternative="NewClass", removal_version="2.0.0")
        class OldClass:
            def __init__(self):
                self.value = "test"

        with pytest.warns(
            DeprecationWarning, match="DEPRECATED: OldClass - This class is deprecated"
        ):
            obj = OldClass()
            assert obj.value == "test"

    def test_deprecated_method_warning(self):
        """Test that calling a deprecated method issues a warning."""

        class MyClass:
            @deprecated("This method is deprecated")
            def old_method(self):
                return "result"

        obj = MyClass()
        with pytest.warns(
            DeprecationWarning, match="DEPRECATED: old_method - This method is deprecated"
        ):
            result = obj.old_method()
            assert result == "result"

    def test_deprecated_message_formatting(self):
        """Test that the deprecation message is formatted correctly."""

        @deprecated("Reason", alternative="Alternative", removal_version="2.0.0")
        def func():
            pass

        with pytest.warns(DeprecationWarning) as record:
            func()

        message = str(record[0].message)
        assert "DEPRECATED: func - Reason" in message
        assert "Use instead: Alternative" in message
        assert "Will be removed in version 2.0.0" in message
