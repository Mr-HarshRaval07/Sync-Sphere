import pytest
from syncsphere.shared_kernel.types.result import Result

def test_result_ok():
    """Tests that Result.ok constructs a successful Result object."""
    res = Result.ok("success_value")
    assert res.is_ok is True
    assert res.is_fail is False
    assert res.value() == "success_value"
    assert res.get_or_else("default") == "success_value"

def test_result_fail():
    """Tests that Result.fail constructs a failure Result object."""
    res = Result.fail("error_value")
    assert res.is_ok is False
    assert res.is_fail is True
    assert res.error() == "error_value"
    assert res.get_or_else("default") == "default"

def test_result_value_exception_on_fail():
    """Tests that calling value() on a failed Result raises ValueError."""
    res = Result.fail("error")
    with pytest.raises(ValueError, match="Cannot retrieve value from an Err Result"):
        res.value()

def test_result_error_exception_on_ok():
    """Tests that calling error() on a successful Result raises ValueError."""
    res = Result.ok("success")
    with pytest.raises(ValueError, match="Cannot retrieve error from an Ok Result"):
        res.error()
