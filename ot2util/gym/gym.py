"""Define Gym interface."""

from typing import Any


class Gym:
    """Gym base class."""

    def __init__(self) -> None:
        pass

    def action(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError

    def state(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError
