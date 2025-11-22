import pytest


if __name__ == "__main__":
    raise SystemExit(
        pytest.main(["-m", "integration", "tests/test_upst_pipeline.py"])
    )
