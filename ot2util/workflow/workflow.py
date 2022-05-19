"""Define Workflow interface."""

from concurrent.futures import Future
from typing import Any, List, Set

from ot2util.experiment import Experiment


class Workflow:
    """Workflow base class."""

    def __init__(self) -> None:
        """Initialize the workflow base class."""
        self.futures: Set[Future[Experiment]] = set()

    def wait(self) -> List[Experiment]:
        """Wait for running experiments to finish.

        Returns
        -------
        List[Experiment]
            List of finished :obj:`Experiment`.
        """
        experiments = [future.result() for future in self.futures]
        self.futures = set()
        return experiments

    def action(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError

    def state(self, *args: Any, **kwargs: Any) -> None:
        """Child class should implement."""
        raise NotImplementedError
