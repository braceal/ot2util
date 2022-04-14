"""Run a grid search to test different volume values.

To run it, update the grid_search.yaml configuration file and run:
python grid_search.py -c grid_search.yaml

See search_results/ for a simulated output.
"""
from pathlib import Path
from typing import List, Optional
from ot2util.config import BaseSettings, parse_args
from ot2util.experiment import Experiment, ExperimentManager
from protocol import SimpleProtocolConfig

import ot2util.camera as camera

import logging

logging.basicConfig()
logging.getLogger("paramiko.transport").setLevel(logging.DEBUG)


class GridSearchConfig(BaseSettings):
    # Remote setup parameters (None if running locally)
    # Remote directory path to stage experiments in
    remote_dir: Optional[Path] = None
    # Remote host i.e. [user@]host[:port]
    host: Optional[str] = None
    # Private key path
    key_filename: Optional[str] = None
    # Path to opentrons_simulate or opentrons_execute directory
    opentrons_path: Path = Path("/usr/bin")
    # Whether or not to tar files before transferring from remote to local
    tar_transfer: bool = False

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
    camera_id : int



def main(cfg: GridSearchConfig):

    # Create output directory for writing results to
    cfg.output_dir.mkdir(exist_ok=True)

    # Create a protocol configuration with default parameters
    protocol_cfg = SimpleProtocolConfig.from_yaml("config.yaml")

    # Initialize Camera
    if not cfg.run_simulation:
        camera.initialize_camera(cfg.camera_id)

    # Creat experiment manager to launch experiments
    experiment_manager = ExperimentManager(
        cfg.run_simulation,
        cfg.host,
        cfg.key_filename,
        cfg.opentrons_path,
        cfg.tar_transfer,
    )

    # Count number of experiments to label directories
    num_experiments = len(str(len(cfg.volume_values)))

    # Loop over specified volume values and update configuration
    for itr, volume in enumerate(cfg.volume_values):
        # Update search parameter
        protocol_cfg.volume = volume

        # Create new experiment
        experiment_name = f"experiment-{itr:0{num_experiments}d}"
        if cfg.remote_dir is not None:
            protocol_cfg.workdir = cfg.remote_dir / experiment_name
        experiment = Experiment(
            experiment_name, cfg.output_dir, cfg.protocol, protocol_cfg
        )

        # Run the experiment
        returncode = experiment_manager.run(experiment)
        # After running the experiment, read the experiment result file
        if not cfg.run_simulation:
            
            camera.color_recognize(Path(cfg.output_dir) / experiment_name, )
        if returncode != 0:
            raise ValueError(f"Experiment {experiment.name} failed to run")


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    main(cfg)
