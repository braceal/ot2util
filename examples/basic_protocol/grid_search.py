"""Run a grid search to test different volume values.

To run it, update the grid_search_[local/remote].yaml configuration file and run:
python grid_search.py -c grid_search_[local/remote].yaml

See search_results/ for a simulated output.
"""
from pathlib import Path
from typing import List
from ot2util.config import ExperimentConfig, parse_args
from ot2util.experiment import Experiment, ExperimentManager
from ot2util.camera import Camera
from protocol import SimpleProtocolConfig


class GridSearchConfig(ExperimentConfig):
    # Path to protocol script containing run function
    protocol: Path = ""
    # Base configuration options for the protocol
    base_config: Path = Path("config.yaml")
    # Volume values to grid search
    volume_values: List[int] = [50, 100]
    # Camera ID
    camera_id: int = 2


def main(cfg: GridSearchConfig):

    # Create output directory for writing results to
    cfg.output_dir.mkdir(exist_ok=True)

    # Create a protocol configuration with default parameters
    protocol_cfg = SimpleProtocolConfig.from_yaml(cfg.base_config)

    # Create experiment manager to launch experiments
    experiment_manager = ExperimentManager(cfg.run_simulation, cfg.robots)

    # Initialize Camera
    if not cfg.run_simulation:
        camera = Camera(cfg.camera_id)

    # Count number of experiments to label directories
    num_experiments = len(str(len(cfg.volume_values)))

    for itr, volume_list in enumerate(cfg.volume_values):
        # Update search parameter
        protocol_cfg.source_volumes = list(volume_list)

        # Create new experiment
        name = f"experiment-{itr:0{num_experiments}d}"
        experiment = Experiment(name, cfg.output_dir, cfg.protocol, protocol_cfg)

        # Run the experiment
        returncode = experiment_manager.run(experiment)
        if returncode != 0:
            raise ValueError(
                f"Experiment {experiment.name} exited with returncode: {returncode}"
            )

        # After running the experiment, read the experiment result file
        if not cfg.run_simulation:
            # Find destination wells and measure their color
            for destination_well in cfg.destination_wells:

                rgb, hsv = camera.measure_well_color(destination_well)
                # TODO: How should we end up storing this information?
                # And how do we make it accessible to an algorithm?
                print(
                    f"Experiment-{itr}: target_well: {destination_well} rgb: {rgb}, hsv: {hsv}"
                )


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    main(cfg)
