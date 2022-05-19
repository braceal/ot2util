"""Run a grid search to test different volume values.

To run it, update the config_[local/remote].yaml configuration file and run:
python agent.py -c config_[local/remote].yaml

See search_results/ for a simulated output.
"""

import itertools
import logging

from ot2util.agent import Agent
from ot2util.config import parse_args
from ot2util.workflow import ColorMixingWorkflow, ColorMixingWorkflowConfig

logger = logging.getLogger("ot2util")


class GridSearchConfig(ColorMixingWorkflowConfig):
    pass


class GridSearch(Agent):
    def __init__(self, config: GridSearchConfig) -> None:
        super().__init__(config)
        self.workflow = ColorMixingWorkflow(config)

    def run(self) -> None:

        # TODO: Assuming volumes are constant for now
        volumes = [10, 10, 10]
        # TODO: Make data structure for colors?
        sourcecolors = ["A1", "A2", "A3", "B1"]
        # Loop over color combinations
        for itr, colors in enumerate(itertools.combinations(sourcecolors, 3)):
            name = f"experiment-{itr:03d}"
            self.workflow.action(name, colors, volumes)
            if (itr + 1) % 2 == 0:
                experiments = self.workflow.wait()
                for experiment in experiments:
                    logger.info(experiment)


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    gridsearch = GridSearch(cfg)
    logger.info("Running gridsearch")
    gridsearch.run()
    logger.info("Done running gridsearch")
