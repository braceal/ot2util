"""Run a grid search to test different volume values.

To run it, update the grid_search.yaml configuration file and run:
python grid_search.py -c grid_search.yaml

See search_results/ for a simulated output.
"""
from pathlib import Path
from typing import List, Optional
from ot2util.config import BaseSettings, parse_args, ExperimentResult
from ot2util.experiment import Experiment, ExperimentManager
from protocol import SimpleProtocolConfig


import numpy as np
import ot2util.camera as camera
import itertools

import logging

logging.basicConfig()
logging.getLogger("paramiko.transport").setLevel(logging.DEBUG)


def next_location(cur_location : str) -> str:
    letter = cur_location[0]
    number = cur_location[1:]
    if number == "12":
        number = "1"
        letter = chr(ord(letter) + 1)
    else:
        number = str(int(number) + 1)
    if letter == "I" and number == "12":
        return ""
    return letter + number

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
    volume_min : int = 5
    volume_max : int = 20
    volume_step : int = 5
    camera_id : int = 2



def main(cfg: GridSearchConfig):

    # Create output directory for writing results to
    cfg.output_dir.mkdir(exist_ok=True)

    # Create a protocol configuration with default parameters
    protocol_cfg = SimpleProtocolConfig.from_yaml("config.yaml")

    
    # Initialize Camera
    if not cfg.run_simulation:
        camera_obj = camera.Camera(cfg.camera_id)

    # Creat experiment manager to launch experiments
    experiment_manager = ExperimentManager(
        cfg.run_simulation,
        cfg.host,
        cfg.key_filename,
        cfg.opentrons_path,
        cfg.tar_transfer,
    )

    # Loop over specified volume values and update configuration
    num_colors = len(protocol_cfg.source_wells)
    volumes = np.arange(cfg.volume_min, cfg.volume_max, cfg.volume_step)
    print(f"volumes: {volumes}")

    for itr, volume_list in enumerate(itertools.permutations(volumes.tolist(), num_colors)):
        # Update search parameter
        protocol_cfg.source_volumes = list(volume_list)
    
        # Create new experiment
        experiment_name = f"experiment-{itr}"
        if cfg.remote_dir is not None:
            protocol_cfg.workdir = cfg.remote_dir / experiment_name
        experiment = Experiment(
            experiment_name, cfg.output_dir, cfg.protocol, protocol_cfg
        )

        # Run the experiment
        returncode = experiment_manager.run(experiment)
        # After running the experiment, read the experiment result file
        if not cfg.run_simulation:
            # Update the protocol configuration with the experiment result
            result = ExperimentResult.from_yaml(cfg.output_dir / experiment_name / "experiment_result.yaml")
            coordinate = camera_obj.convert_coordinate(result.cur_target_well)
            RGB_value, HSV_value = camera_obj.color_recognize(Path(cfg.output_dir) / experiment_name, coordinate, itr)
            protocol_cfg.target_tip = result.next_target_tip
            protocol_cfg.target_well = result.next_target_well
            print(f"Experiment-{iter}: target_well: {result.cur_target_well} RGB_value: {RGB_value}, HSV_value: {HSV_value}")
        if returncode != 0:
            raise ValueError(f"Experiment {experiment.name} failed to run")


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    main(cfg)
