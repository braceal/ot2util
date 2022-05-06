from typing import Any, Optional
from ot2util.config import ExperimentConfig
from ot2util.experiment import ExperimentManager


class Algorithm:
    """Base class for user implemented search algorithms.
    Users should implement `run()`"""

    def __init__(self, config: ExperimentConfig) -> None:
        """Initialize the algorithm, store the config as a property,
        and connect to any robots requested.

        Parameters
        ----------
        config : ExperimentConfig
            An experiment config which contains options for connecting
            to robots, and algorithm parameters helpful to the user.
        """
        self.config = config
        # Create experiment manager to connect to robots
        self.experiment_manager = ExperimentManager(
            self.config.run_simulation, self.config.robots
        )
        # Make output folder
        self.config.output_dir.mkdir(exist_ok=True)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.config})"

    def run(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """User should implement this."""
        raise NotImplementedError
