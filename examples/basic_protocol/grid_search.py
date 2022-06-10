"""Run a grid search to test different volume values.

To run it, update the grid_search_[local/remote].yaml configuration file and run:
python grid_search_agent.py -c grid_search_[local/remote].yaml

See search_results/ for a simulated output.
"""
from pathlib import Path
from typing import List

from protocol import SimpleProtocolConfig

from ot2util.agent import Agent
from ot2util.camera import Camera
from ot2util.config import parse_args
from ot2util.experiment import Experiment
from ot2util.workflow import ColorMixingWorkflow, ColorMixingWorkflowConfig

import numpy as np
import itertools
import logging
import cv2

logger = logging.getLogger("ot2util")

class GridSearchConfig(ColorMixingWorkflowConfig):
    # Path to protocol script containing run function
    protocol: Path = ""
    # Base configuration options for the protocol
    base_config: Path = Path("config.yaml")
    # whether to run simulation
    run_simulation: bool = False
    # output_dir
    output_dir: Path = ""
    # Camera ID
    camera_id: int = 2
    # Volume search settings
    volume_min : int = 5
    volume_max : int = 20
    volume_step : int = 5


# TODO: This example is now broken, needs update to new interface.
#       It will probably be easier to delete and use newer example version.
class GridSearch(Agent):
    def __init__(self, config: GridSearchConfig) -> None:
        # Creates self.config, self.robot_pool fields
        super().__init__(config)

        self.config = config
        # Number of unique experiments to run
        self.volumes = np.arange(self.config.volume_min, self.config.volume_max, self.config.volume_step)
        self.protocol_cfg = SimpleProtocolConfig.from_yaml(self.config.base_config)
        self.num_colors = len(self.protocol_cfg.source_volumes)
        self.experiments = list(enumerate(itertools.permutations(self.volumes.tolist(), self.num_colors)))
        self.num_experiments = len(self.experiments)
        self.workflow = ColorMixingWorkflow(config)

    def run(self) -> None:

        # Loop over specified volume values, update configuration, launch experiment
        for itr, volume_list in self.experiments:
            self.protocol_cfg.source_volumes = list(volume_list)
            # Create new experiment
            name = f"experiment-{itr:0{self.num_experiments}d}"
            self.workflow.action(name, self.protocol_cfg.source_wells, self.protocol_cfg.source_volumes)
            experiments = self.workflow.wait()
            for experiment in experiments:
                print(f"RGB color for {experiment.result['target_well']}:{experiment.result['rgb']}")
                cv2.imwrite(str(self.config.output_dir / (name + "/frame_org.png")), experiment.result["org_frame"])
                cv2.imwrite(str(self.config.output_dir / (name + "/frame_with_marker1.png")), experiment.result["frame_with_marker1"])
                cv2.imwrite(str(self.config.output_dir / (name + "/frame_with_marker2.png")), experiment.result["frame_with_marker2"])
                logger.info(experiment)


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    gridsearch = GridSearch(cfg)
    print("Running gridsearch")
    gridsearch.run()
    print("Done running gridsearch")
