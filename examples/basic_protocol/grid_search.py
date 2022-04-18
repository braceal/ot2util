"""Run a grid search to test different volume values.

To run it, update the grid_search.yaml configuration file and run:
python grid_search.py -c grid_search.yaml

See search_results/ for a simulated output.
"""
from pathlib import Path
from typing import List
from ot2util.config import BaseSettings, OpentronsConfig, parse_args
from ot2util.experiment import Experiment, ExperimentManager
from protocol import SimpleProtocolConfig

import logging

logging.basicConfig()
logging.getLogger("paramiko.transport").setLevel(logging.DEBUG)


class GridSearchConfig(BaseSettings):
    # Connect to one (or many) OT-2s
    robots: List[OpentronsConfig] = []
    # Directory to write experimental results to
    output_dir: Path = ""
    # Path to protocol script containing run function
    protocol: Path = ""
    # TODO: Add this protocol config here
    # Configuration of the protocol
    # protocol: SimpleProtocolConfig
    # Toggle simulation
    run_simulation: bool = True
    # Volume values to grid search
    volume_values: List[int] = [50, 100]


def main(cfg: GridSearchConfig):

    # Create output directory for writing results to
    cfg.output_dir.mkdir(exist_ok=True)

    # Create a protocol configuration with default parameters
    protocol_cfg = SimpleProtocolConfig.from_yaml("config.yaml")

    # Creat experiment manager to launch experiments
    experiment_manager = ExperimentManager(cfg.run_simulation, cfg.robots)

    # Count number of experiments to label directories
    num_experiments = len(str(len(cfg.volume_values)))

    # Loop over specified volume values and update configuration
    for itr, volume in enumerate(cfg.volume_values):
        # Update search parameter
        protocol_cfg.volume = volume

        # Create new experiment
        name = f"experiment-{itr:0{num_experiments}d}"
        experiment = Experiment(name, cfg.output_dir, cfg.protocol, protocol_cfg)

        # Run the experiment
        returncode = experiment_manager.run(experiment)
        if returncode != 0:
            raise ValueError(
                f"Experiment {experiment.name} exited with returncode: {returncode}"
            )


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    main(cfg)
