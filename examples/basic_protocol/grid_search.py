"""Run a grid search to test different volume values.

To run it, update the grid_search.yaml configuration file and run:
python grid_search.py -c grid_search.yaml

See search_results/ for a simulated output.
"""
from pathlib import Path
from typing import List
from ot2util.config import BaseSettings, parse_args
from ot2util.experiment import Experiment, ExperimentManager
from protocol import ProtocolConfig


class GridSearchConfig(BaseSettings):

    # Directory to write experimental results to
    output_dir: Path = ""
    # Path to protocol script containing run function
    protocol_script_path: Path = ""
    # Toggle simulation
    run_simulation: bool = True
    # Volume values to grid search
    volume_values: List[int] = [50, 100]


def main(cfg: GridSearchConfig):

    # Create output directory for writing results to
    cfg.output_dir.mkdir(exist_ok=True)

    # Create a protocol configuration with default parameters
    protocol_cfg = ProtocolConfig()

    # Creat experiment manager to launch experiments
    experiment_manager = ExperimentManager(cfg.run_simulation)

    # Count number of experiments to label directories
    num_experiments = len(str(len(cfg.volume_values)))

    # Loop over specified volume values and update configuration
    for itr, volume in enumerate(cfg.volume_values):
        # Update search parameter
        protocol_cfg.volume = volume

        # Create new experiment
        experiment_name = f"experiment-{itr:0{num_experiments}d}"
        experiment = Experiment(
            experiment_name, cfg.output_dir, cfg.protocol_script_path, protocol_cfg
        )

        # Run the experiment
        experiment_manager.run(experiment)


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    main(cfg)
