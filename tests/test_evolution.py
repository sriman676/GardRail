import os
import pytest
from unittest.mock import MagicMock, patch

from core.evolution import SystemOptimizer


def test_update_env_threshold(tmp_path):
    optimizer = SystemOptimizer()
    
    # Mock writing to a temporary test .env file
    test_env = tmp_path / ".env"
    with open(test_env, "w", encoding="utf-8") as f:
        f.write("DRIFT_THRESHOLD=0.70\nOTHER_SETTING=123\n")

    # Patch the method's target path
    with patch("core.evolution.os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()) as mock_open:
            # Setup read content
            mock_file = MagicMock()
            mock_file.read.return_value = "DRIFT_THRESHOLD=0.70\nOTHER_SETTING=123\n"
            mock_open.return_value.__enter__.return_value = mock_file

            success = optimizer._update_env_threshold(0.85)

            assert success is True
            # Verify open was called to write the new threshold
            mock_open.assert_called()


def test_apply_new_rules():
    optimizer = SystemOptimizer()
    
    # Verify regex compilation validation checks
    malformed_rule = {"pattern": "[unclosed bracket", "pattern_id": "EVOLVED_999", "explanation": "test"}
    valid_rule = {"pattern": "override instructions", "pattern_id": "EVOLVED_001", "explanation": "test"}
    
    with patch("core.evolution.os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = "INJECTION_PATTERNS = [\n]"
            mock_open.return_value.__enter__.return_value = mock_file

            # Patch active scanner patterns to prevent write-back changes to real module
            with patch("core.injection_scanner.INJECTION_PATTERNS", []):
                # Try to apply both rules
                added = optimizer._apply_new_rules([malformed_rule, valid_rule])
                
                # Malformed should be rejected, valid should be accepted
                assert added == 1
