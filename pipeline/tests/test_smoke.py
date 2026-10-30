"""Smoke test: proves pytest can find and import the pipeline package."""
import mrw


def test_package_imports():
    assert mrw.__version__ == "0.1.0"
