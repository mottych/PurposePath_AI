import pytest
from coaching.src.core import interaction_codes

pytestmark = pytest.mark.unit


class TestInteractionCodes:
    """Test suite for interaction codes."""

    def test_constants_are_strings(self):
        """Test that all constants are strings."""
        # Get all public attributes that are uppercase (constants)
        constants = [
            getattr(interaction_codes, name)
            for name in dir(interaction_codes)
            if name.isupper() and not name.startswith("_")
        ]

        for constant in constants:
            assert isinstance(constant, str)
            assert len(constant) > 0

    def test_specific_codes_exist(self):
        """Test that key interaction codes exist."""
        assert interaction_codes.ALIGNMENT_ANALYSIS == "ALIGNMENT_ANALYSIS"
        assert interaction_codes.COACHING_RESPONSE == "COACHING_RESPONSE"
        assert interaction_codes.STRATEGIC_ALIGNMENT == "STRATEGIC_ALIGNMENT"
