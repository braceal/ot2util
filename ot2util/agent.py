"""Base class for implementing your own search agents on the OT2."""
from typing import Any, Optional

from ot2util.config import WorkflowConfig


class Agent:
    """Base class for user implemented search agents.
    Users should implement `run()`"""

    def __init__(self, config: WorkflowConfig) -> None:
        """Initialize the agent, store the config as a property,
        and connect to any robots requested.

        Parameters
        ----------
        config : WorkflowConfig
            An experiment config which contains options for connecting
            to robots, and agent parameters helpful to the user.
        """
        self.config = config
        # Make output folder
        self.config.output_dir.mkdir(exist_ok=True)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.config})"

    def run(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """User should implement this."""
        raise NotImplementedError
