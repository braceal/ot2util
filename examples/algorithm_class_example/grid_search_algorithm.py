"""Run a grid search to test different volume values.

To run it, update the grid_search_[local/remote].yaml configuration file and run:
python grid_search_algorithm.py -c grid_search_[local/remote].yaml

See search_results/ for a simulated output.
"""

from typing import List
from pathlib import Path
from ot2util.algorithm import Algorithm
from ot2util.experiment import Experiment
from ot2util.config import parse_args, ExperimentConfig
from protocol import SimpleProtocolConfig


class GridSearchConfig(ExperimentConfig):
    # Path to protocol script containing run function
    protocol: Path = ""
    # Base configuration options for the protocol
    base_config: Path = Path("config.yaml")
    # Volume values to grid search
    volume_values: List[int] = [50, 100]


class GridSearch(Algorithm):
    def __init__(self, config: GridSearchConfig) -> None:
        # Creates self.config, self.experiment_manager fields
        super().__init__(config)

        # Number of unique experiments to run
        self.num_experiments = len(str(len(self.config.volume_values)))

    def run(self) -> None:

        # Loop over specified volume values, update configuration, launch experiment
        for itr, volume in enumerate(self.config.volume_values):
            # Create a fresh protocol config for individual experiment
            protocol_cfg = SimpleProtocolConfig.from_yaml(self.config.base_config)

            # Update search parameter
            protocol_cfg.volume = volume

            # Create new experiment
            name = f"experiment-{itr:0{self.num_experiments}d}"
            experiment = Experiment(
                name, self.config.output_dir, self.config.protocol, protocol_cfg
            )

            # Run the experiment
            returncode = self.experiment_manager.run(experiment)
            if returncode != 0:
                raise ValueError(
                    f"Experiment {experiment.name} exited with returncode: {returncode}"
                )


def main(cfg: GridSearchConfig):
    gridsearch = GridSearch(cfg)
    print("Running gridsearch")
    gridsearch.run()
    print("Done running gridsearch")


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    main(cfg)
