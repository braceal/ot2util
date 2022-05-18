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
from ot2util.config import WorkflowConfig, parse_args
from ot2util.experiment import Experiment


class GridSearchConfig(WorkflowConfig):
    # Path to protocol script containing run function
    protocol: Path = ""
    # Base configuration options for the protocol
    base_config: Path = Path("config.yaml")
    # Volume values to grid search
    volume_values: List[int] = [50, 100]
    # Camera ID
    camera_id: int = 2


# TODO: This example is now broken, needs update to new interface.
#       It will probably be easier to delete and use newer example version.
class GridSearch(Agent):
    def __init__(self, config: GridSearchConfig) -> None:
        # Creates self.config, self.robot_pool fields
        super().__init__(config)

        # Number of unique experiments to run
        self.num_experiments = len(str(len(self.config.volume_values)))

        # Initialize Camera
        if not self.config.run_simulation:
            self.camera = Camera(cfg.camera_id)

    def run(self) -> None:

        # Loop over specified volume values, update configuration, launch experiment
        for itr, volume in enumerate(self.config.volume_values):
            # Create a fresh protocol config for individual experiment
            protocol_cfg = SimpleProtocolConfig.from_yaml(self.config.base_config)

            # Update search parameter
            protocol_cfg.source_volumes = list(volume)

            # Create new experiment
            name = f"experiment-{itr:0{self.num_experiments}d}"
            experiment = Experiment(
                name, self.config.output_dir, self.config.protocol, protocol_cfg
            )
            print("Launching experiment:", itr)
            returncode = self.submit(experiment)
            print("itr:", itr, returncode)

            # After running the experiment, read the experiment result file
            if not cfg.run_simulation:
                # Find destination wells and measure their color
                for destination_well in cfg.destination_wells:

                    rgb, hsv = self.camera.measure_well_color(destination_well)
                    # TODO: How should we end up storing this information?
                    # And how do we make it accessible to the agent?
                    print(
                        f"Experiment-{itr}: target_well: {destination_well} rgb: {rgb}, hsv: {hsv}"
                    )


def main(cfg: GridSearchConfig):

    for itr, volume_list in enumerate(cfg.volume_values):
        # Update search parameter
        # protocol_cfg.source_volumes = list(volume_list)
        print(itr, volume_list)


if __name__ == "__main__":
    args = parse_args()
    cfg = GridSearchConfig.from_yaml(args.config)
    gridsearch = GridSearch(cfg)
    print("Running gridsearch")
    gridsearch.run()
    print("Done running gridsearch")
