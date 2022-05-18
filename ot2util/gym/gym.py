"""Define Gym interface."""

from concurrent.futures import Future
from typing import Any, List, Set

from ot2util.experiment import Experiment


class Gym:
    """Gym base class."""

    def __init__(self) -> None:
        self.futures: Set[Future[int]] = set()

    def wait(self) -> List[Experiment]:
        experiments = [future.result() for future in self.futures]
        self.futures = set()
        return experiments

    def action(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError

    def state(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError
