from typing import Generic, TypeVar, Union, Optional

T = TypeVar("T")
E = TypeVar("E")

class Result(Generic[T, E]):
    """
    A monadic representation of an operation's outcome.
    Can either be Ok (containing the successful value) or Err (containing the error object).
    """
    
    def __init__(self, value: Union[T, E], is_ok: bool) -> None:
        self._value = value
        self._is_ok = is_ok

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """Constructs an Ok Result containing the successful value."""
        return cls(value, is_ok=True)

    @classmethod
    def fail(cls, error: E) -> "Result[T, E]":
        """Constructs an Err Result containing the error/exception."""
        return cls(error, is_ok=False)

    @property
    def is_ok(self) -> bool:
        """Returns True if the result is successful."""
        return self._is_ok

    @property
    def is_fail(self) -> bool:
        """Returns True if the result represents a failure."""
        return not self._is_ok

    def value(self) -> T:
        """
        Retrieves the successful value.
        Raises a ValueError if the result represents a failure.
        """
        if not self._is_ok:
            raise ValueError(f"Cannot retrieve value from an Err Result: {self._value}")
        return self._value  # type: ignore

    def error(self) -> E:
        """
        Retrieves the error object.
        Raises a ValueError if the result represents a success.
        """
        if self._is_ok:
            raise ValueError("Cannot retrieve error from an Ok Result.")
        return self._value  # type: ignore

    def get_or_else(self, default: T) -> T:
        """Returns the inner value if Ok, otherwise returns the default value."""
        if self._is_ok:
            return self._value  # type: ignore
        return default
