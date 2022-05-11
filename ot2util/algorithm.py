"""Abstract class usefull for implementing your own search algorithms on the OT2.
"""

from typing import Any, Optional, List
from ot2util.config import ExperimentConfig
from ot2util.experiment import ExperimentManager, Experiment
from concurrent.futures import ThreadPoolExecutor, Future, wait


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

        # TODO: Probably move pool logic to gym
        self.pool = ThreadPoolExecutor(max_workers=len(self.config.robots) + 1)

    def submit(self, experiment: Experiment) -> Future[int]:
        fut = self.pool.submit(self._submit, experiment)
        if len(self.config.robots) == 1:
            # wait returns a named tuple of futures wait().done is
            # a set of completed futures and since we only have a single
            # thread in this case, it will have one element so we pop it
            # from the set and return the Future.
            return wait([fut]).done.pop()
        return fut

    def submit_batch(self, experiments: List[Experiment]) -> List[Future[int]]:
        return [self.submit(experiment) for experiment in experiments]

    def _submit(self, experiment: Experiment) -> int:
        # Run the experiment
        returncode = self.experiment_manager.run(experiment)
        if returncode != 0:
            raise ValueError(
                f"Experiment {experiment.name} exited with returncode: {returncode}"
            )
        return returncode

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.config})"

    def run(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """User should implement this."""
        raise NotImplementedError
