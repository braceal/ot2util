"""Define Workflow interface."""

from typing import Any


class Workflow:
    """Workflow base class."""

    def __init__(self) -> None:
        """Initialize the workflow base class."""

    def action(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError

    def state(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError
