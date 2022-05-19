"""A workflow for color mixing protocols."""
import logging
from pathlib import Path
from typing import List

from opentrons.protocol_api import ProtocolContext

from ot2util.config import (
    InstrumentConfig,
    LabwareConfig,
    OpentronsRobotConfig,
    ProtocolConfig,
    WorkflowConfig,
)
from ot2util.experiment import Experiment, OpenTronsRobot, RobotPool
from ot2util.labware import TipRack, WellPlate
from ot2util.workflow.workflow import Workflow

logger = logging.getLogger(__name__)


class ColorMixingProtocolConfig(ProtocolConfig):
    # File must be named config
    source_wells: List[str] = ["A1", "A2", "A3"]
    source_volumes: List[int] = [10, 5, 10]
    # Volume to aspirate and dispense
    tips: List[str] = ["A1", "A2", "A3"]
    """Each experiment needs to specify all of the tips it
    will use to mix the three colors."""
    target_well: str = "B1"
    wellplate: LabwareConfig
    tiprack: LabwareConfig
    pipette: InstrumentConfig
    sourceplate: LabwareConfig


class ColorMixingRobotConfig(OpentronsRobotConfig):
    wellplate: LabwareConfig = LabwareConfig(
        name="corning_96_wellplate_360ul_flat", location="2"
    )
    tiprack: LabwareConfig = LabwareConfig(
        name="opentrons_96_tiprack_300ul", location="1"
    )
    pipette: InstrumentConfig = InstrumentConfig(name="p300_single", mount="left")
    sourceplate: LabwareConfig = LabwareConfig(
        name="corning_6_wellplate_16.8ml_flat", location="3"
    )
    # TODO: Add camera config


class ColorMixingWorkflowConfig(WorkflowConfig):
    robots: List[ColorMixingRobotConfig] = []  # type: ignore[assignment]


class ColorMixingRobot(OpenTronsRobot):
    protocol_config_class = ColorMixingProtocolConfig  # type: ignore[assignment]

    def __init__(self, config: ColorMixingRobotConfig, output_dir: Path):
        super().__init__(config)
        self.config = config
        self.output_dir = output_dir
        self.wellplate = WellPlate()
        self.tiprack = TipRack()
        # TODO: Implement the camera
        self.camera = None

    def setup_experiment(
        self, name: str, source_wells: List[str], source_volumes: List[str]
    ) -> Experiment:

        target_well = self.wellplate.get_open_well()
        tips = self.tiprack.get_tips(n=3)

        # TODO: Perhaps allow user to interact at this point
        if target_well is None:
            raise ValueError("wellplate full")
        if tips is None:
            raise ValueError("no tips available")

        config = ColorMixingProtocolConfig(
            source_wells=source_wells,
            source_volumes=source_volumes,
            tips=tips,
            target_well=target_well,
            wellplate=self.config.wellplate,
            tiprack=self.config.tiprack,
            pipette=self.config.pipette,
            sourceplate=self.config.sourceplate,
        )

        # Create new experiment
        experiment = Experiment(name, self.output_dir, config)

        # TODO: Change function name to generate_protocol
        self.generate_template(experiment.protocol)
        return experiment

    def post_experiment(
        self, experiment: Experiment, source_wells: List[str], source_volumes: List[str]
    ) -> None:
        # TODO: Take picture with camera.
        return None

    def imports(self) -> None:
        """This protocol implements the color mixing workflow."""
        from typing import List  # noqa

        from opentrons.protocol_api import ProtocolContext  # noqa

        from ot2util.config import InstrumentConfig  # noqa
        from ot2util.config import LabwareConfig  # noqa
        from ot2util.config import ProtocolConfig  # noqa

    def run(protocol: ProtocolContext) -> None:  # type: ignore[misc]

        # Load the protocol configuration
        cfg = ColorMixingProtocolConfig.get_config(protocol)

        # labware
        wellplate = protocol.load_labware(cfg.wellplate.name, cfg.wellplate.location)
        tiprack = protocol.load_labware(cfg.tiprack.name, cfg.tiprack.location)
        sourceplate = protocol.load_labware(
            cfg.sourceplate.name, cfg.sourceplate.location
        )

        # pipettes
        pipette = protocol.load_instrument(
            cfg.pipette.name, cfg.pipette.mount, tip_racks=[tiprack]
        )

        # commands
        for src_well, src_volume, tip in zip(
            cfg.source_wells, cfg.source_volumes, cfg.tips
        ):
            pipette.pick_up_tip(location=tiprack.wells_by_name()[tip])
            pipette.aspirate(src_volume, sourceplate[src_well])
            pipette.dispense(src_volume, wellplate[cfg.target_well])
            pipette.drop_tip()


class ColorMixingWorkflow(Workflow):
    def __init__(self, config: ColorMixingWorkflowConfig) -> None:
        super().__init__()
        self.robots = [
            ColorMixingRobot(robot, config.output_dir) for robot in config.robots
        ]
        self.robot_pool = RobotPool(self.robots)  # type: ignore[arg-type]

    def action(self, name: str, colors: List[str], volumes: List[str]) -> None:
        # TODO: Color is probably a data type with name and location (Namedtuple).
        #       Suppose for now they are location names e.g. "A1"

        logger.info(f"Launching experiment: {name}")
        future = self.robot_pool.submit(
            name=name, source_wells=colors, source_volumes=volumes
        )
        # experiment = future.result()
        # logger.info(f"Experiment {name} finished with returncode: {returncode}")

    def state(self) -> None:  # noqa
        # TODO: Retrieve camera values
        return None
